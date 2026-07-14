# pyrefly: ignore [missing-import]
import numpy as np

class BeamSolver:
    def __init__(self):
        pass

    @staticmethod
    def compute_fem(length, EI, loads):
        """
        Calculate Fixed End Moments (FEM) for a single span.
        Clockwise moment acting on member end is positive.
        Under downward loads:
          Left support FEM (fem_l) is counter-clockwise, so negative.
          Right support FEM (fem_r) is clockwise, so positive.
        """
        fem_l = 0.0
        fem_r = 0.0
        L = float(length)

        for load in loads:
            load_type = load.get('type')
            if load_type == 'Point':
                P = float(load.get('P', 0.0))
                a = float(load.get('a', 0.0))
                b = L - a
                if a < 0 or a > L:
                    continue
                # FEM formulas for point load
                fem_l += - (P * a * (b ** 2)) / (L ** 2)
                fem_r += (P * (a ** 2) * b) / (L ** 2)

            elif load_type == 'UDL':
                w = float(load.get('w', 0.0))
                # If start/end positions not specified, assume full span
                a = float(load.get('a', 0.0))
                b = float(load.get('b', L))
                if a > b:
                    a, b = b, a
                a = max(0.0, min(a, L))
                b = max(0.0, min(b, L))

                # Integrate point load formula over [a, b] for UDL
                # Left end FEM: -w/L^2 * [x^2 * L^2 / 2 - 2 * x^3 * L / 3 + x^4 / 4] evaluated from a to b
                def f_left(x):
                    return (x**2 * L**2 / 2.0) - (2.0 * x**3 * L / 3.0) + (x**4 / 4.0)

                # Right end FEM: w/L^2 * [x^3 * L / 3 - x^4 / 4] evaluated from a to b
                def f_right(x):
                    return (x**3 * L / 3.0) - (x**4 / 4.0)

                fem_l += - (w / (L**2)) * (f_left(b) - f_left(a))
                fem_r += (w / (L**2)) * (f_right(b) - f_right(a))

        return fem_l, fem_r

    @staticmethod
    def solve(spans, support_conditions, tolerance=0.001, max_iter=200):
        """
        Solves the continuous beam using the Moment Distribution Method.
        
        Parameters:
          spans: List of dicts, each containing:
                 'L': length of span (m)
                 'EI': flexural rigidity (kNm^2)
                 'loads': list of loads on this span
          support_conditions: List of strings for each support from 0 to N.
                              Options: 'Fixed', 'Pinned', 'Continuous'
                              Note: Interior supports default to 'Continuous'.
        Returns:
          results: Dict containing final moments, reactions, and detailed iteration steps.
        """
        N = len(spans)
        if len(support_conditions) != N + 1:
            raise ValueError(f"Number of support conditions must be N+1 ({N+1}), but got {len(support_conditions)}.")

        # Compute relative stiffnesses K
        K = [float(span['EI']) / float(span['L']) for span in spans]

        # Initialize distribution factors (DF)
        # DF_left[j] is the distribution factor for the left member (span j-1) at joint j (for j > 0)
        # DF_right[j] is the distribution factor for the right member (span j) at joint j (for j < N)
        DF_left = [0.0] * (N + 1)
        DF_right = [0.0] * (N + 1)

        # Boundary Joint 0
        if support_conditions[0] == 'Fixed':
            DF_right[0] = 0.0
        else:  # Pinned / Hinged / Continuous
            DF_right[0] = 1.0

        # Boundary Joint N
        if support_conditions[N] == 'Fixed':
            DF_left[N] = 0.0
        else:  # Pinned / Hinged / Continuous
            DF_left[N] = 1.0

        # Interior Joints 1 to N-1
        for j in range(1, N):
            cond = support_conditions[j]
            if cond == 'Fixed':
                # Fully clamped intermediate joint (rare but possible, isolates spans)
                DF_left[j] = 0.0
                DF_right[j] = 0.0
            else:
                # Pinned or Continuous intermediate support
                # Member stiffnesses meeting at joint j:
                # Left: span j-1, stiffness is 4 * K[j-1]
                # Right: span j, stiffness is 4 * K[j]
                k_l = 4.0 * K[j-1]
                k_r = 4.0 * K[j]
                DF_left[j] = k_l / (k_l + k_r)
                DF_right[j] = k_r / (k_l + k_r)

        # Initialize moments to FEMs
        M_L = [0.0] * N
        M_R = [0.0] * N
        for i in range(N):
            fem_l, fem_r = BeamSolver.compute_fem(spans[i]['L'], spans[i]['EI'], spans[i]['loads'])
            M_L[i] = fem_l
            M_R[i] = fem_r

        # Steps log for visual output
        # Format: {'Step': str, 'M_L': list, 'M_R': list, 'M_L_inc': list, 'M_R_inc': list}
        steps_log = []
        steps_log.append({
            'Step': 'Initial FEM',
            'M_L': list(M_L),
            'M_R': list(M_R),
            'M_L_inc': list(M_L),
            'M_R_inc': list(M_R)
        })

        converged = False
        for iter_idx in range(1, max_iter + 1):
            # 1. Calculate out-of-balance moments at joints
            U = [0.0] * (N + 1)
            U[0] = M_L[0]
            U[N] = M_R[N-1]
            for j in range(1, N):
                U[j] = M_R[j-1] + M_L[j]

            # Check convergence
            active_unbalanced = []
            for j in range(N + 1):
                if j == 0:
                    val = abs(U[0]) * DF_right[0]
                elif j == N:
                    val = abs(U[N]) * DF_left[N]
                else:
                    val = abs(U[j]) * max(DF_left[j], DF_right[j])
                active_unbalanced.append(val)

            max_unbalanced = max(active_unbalanced)
            if max_unbalanced < tolerance:
                converged = True
                break

            # 2. Distribute moments
            dm_left = [0.0] * (N + 1)   # Change applied to left member of joint (span j-1 right end)
            dm_right = [0.0] * (N + 1)  # Change applied to right member of joint (span j left end)
            for j in range(N + 1):
                dm_left[j] = -U[j] * DF_left[j]
                dm_right[j] = -U[j] * DF_right[j]

            # Apply distributions
            for i in range(N):
                M_L[i] += dm_right[i]
                M_R[i] += dm_left[i+1]

            # Incremental changes for this balance step
            M_L_inc_bal = [dm_right[i] for i in range(N)]
            M_R_inc_bal = [dm_left[i+1] for i in range(N)]

            steps_log.append({
                'Step': f'Balance {iter_idx}',
                'M_L': list(M_L),
                'M_R': list(M_R),
                'M_L_inc': M_L_inc_bal,
                'M_R_inc': M_R_inc_bal
            })

            # 3. Carry over
            co_L = [0.0] * N
            co_R = [0.0] * N
            for i in range(N):
                co_L[i] = 0.5 * dm_left[i+1]
                co_R[i] = 0.5 * dm_right[i]

            # Apply carry over
            for i in range(N):
                M_L[i] += co_L[i]
                M_R[i] += co_R[i]

            steps_log.append({
                'Step': f'Carry Over {iter_idx}',
                'M_L': list(M_L),
                'M_R': list(M_R),
                'M_L_inc': list(co_L),
                'M_R_inc': list(co_R)
            })

        # Calculate Reactions
        # Free reactions first
        R_free_L = [0.0] * N
        R_free_R = [0.0] * N
        for i in range(N):
            L = float(spans[i]['L'])
            for load in spans[i]['loads']:
                load_type = load.get('type')
                if load_type == 'Point':
                    P = float(load.get('P', 0.0))
                    a = float(load.get('a', 0.0))
                    R_free_L[i] += P * (L - a) / L
                    R_free_R[i] += P * a / L
                elif load_type == 'UDL':
                    w = float(load.get('w', 0.0))
                    a = float(load.get('a', 0.0))
                    b = float(load.get('b', L))
                    if a > b:
                        a, b = b, a
                    a = max(0.0, min(a, L))
                    b = max(0.0, min(b, L))
                    W = w * (b - a)
                    centroid = (a + b) / 2.0
                    R_free_L[i] += W * (L - centroid) / L
                    R_free_R[i] += W * centroid / L

        # Support reaction adjustments
        R_support_L = [0.0] * N
        R_support_R = [0.0] * N
        for i in range(N):
            L = float(spans[i]['L'])
            # Left adjustment is - (M_L + M_R) / L
            # Right adjustment is (M_L + M_R) / L
            # Under standard clockwise positive
            R_support_L[i] = - (M_L[i] + M_R[i]) / L
            R_support_R[i] = (M_L[i] + M_R[i]) / L

        # Combine to get total end shear/reactions per span
        R_span_L = [R_free_L[i] + R_support_L[i] for i in range(N)]
        R_span_R = [R_free_R[i] + R_support_R[i] for i in range(N)]

        # Support Reactions
        support_reactions = [0.0] * (N + 1)
        support_reactions[0] = R_span_L[0]
        support_reactions[N] = R_span_R[N-1]
        for j in range(1, N):
            support_reactions[j] = R_span_R[j-1] + R_span_L[j]

        return {
            'M_L': M_L,
            'M_R': M_R,
            'R_span_L': R_span_L,
            'R_span_R': R_span_R,
            'support_reactions': support_reactions,
            'steps_log': steps_log,
            'converged': converged,
            'iterations': len(steps_log) // 2,
            'DF_left': DF_left,
            'DF_right': DF_right
        }

    @staticmethod
    def get_internal_forces(spans, solved_results, num_points=100):
        """
        Generates shear force and bending moment distributions along the entire beam.
        
        Parameters:
          spans: List of span configurations.
          solved_results: Output of BeamSolver.solve().
          num_points: Number of evaluation points per span.
        Returns:
          data: Dict with x, bending_moment, shear_force, free_moment, support_moment arrays.
        """
        N = len(spans)
        M_L = solved_results['M_L']
        M_R = solved_results['M_R']

        x_global_offset = 0.0
        
        all_x = []
        all_m = []
        all_v = []
        all_m_free = []
        all_m_support = []
        
        span_boundaries = [0.0]

        for i in range(N):
            L = float(spans[i]['L'])
            xs = np.linspace(0, L, num_points)
            
            # Compute support moment line for this span:
            # M_support(x) = M_L*(1 - x/L) - M_R*(x/L)
            m_support = M_L[i] * (1.0 - xs / L) - M_R[i] * (xs / L)
            v_support = - (M_L[i] + M_R[i]) / L
            
            # Compute free moment and free shear
            m_free = []
            v_free = []
            
            # We can calculate the simple beam reaction for free diagrams
            # (which we already have in solved_results, or we can compute it on the fly)
            loads = spans[i]['loads']
            
            # Compute simple beam reactions for loads on this span
            R_free_L_span = 0.0
            for load in loads:
                load_type = load.get('type')
                if load_type == 'Point':
                    P = float(load.get('P', 0.0))
                    a = float(load.get('a', 0.0))
                    R_free_L_span += P * (L - a) / L
                elif load_type == 'UDL':
                    w = float(load.get('w', 0.0))
                    a = float(load.get('a', 0.0))
                    b = float(load.get('b', L))
                    if a > b:
                        a, b = b, a
                    a = max(0.0, min(a, L))
                    b = max(0.0, min(b, L))
                    W = w * (b - a)
                    centroid = (a + b) / 2.0
                    R_free_L_span += W * (L - centroid) / L
            
            for x in xs:
                # Free moments and shear at local x
                m_f = R_free_L_span * x
                v_f = R_free_L_span
                
                for load in loads:
                    load_type = load.get('type')
                    if load_type == 'Point':
                        P = float(load.get('P', 0.0))
                        a = float(load.get('a', 0.0))
                        if x > a:
                            m_f -= P * (x - a)
                            v_f -= P
                    elif load_type == 'UDL':
                        w = float(load.get('w', 0.0))
                        a = float(load.get('a', 0.0))
                        b = float(load.get('b', L))
                        if a > b:
                            a, b = b, a
                        a = max(0.0, min(a, L))
                        b = max(0.0, min(b, L))
                        
                        if x > a:
                            L_act = min(x, b) - a
                            W_act = w * L_act
                            centroid_act = a + L_act / 2.0
                            m_f -= W_act * (x - centroid_act)
                            v_f -= W_act
                            
                m_free.append(m_f)
                v_free.append(v_f)
                
            m_free = np.array(m_free)
            v_free = np.array(v_free)
            
            # Combine to get total forces
            m_total = m_free + m_support
            v_total = v_free + v_support
            
            all_x.extend(xs + x_global_offset)
            all_m.extend(m_total)
            all_v.extend(v_total)
            all_m_free.extend(m_free)
            all_m_support.extend(m_support)
            
            x_global_offset += L
            span_boundaries.append(x_global_offset)

        return {
            'x': all_x,
            'bending_moment': all_m,
            'shear_force': all_v,
            'free_moment': all_m_free,
            'support_moment': all_m_support,
            'span_boundaries': span_boundaries
        }
