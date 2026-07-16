import unittest
from solver import BeamSolver

class TestBeamSolver(unittest.TestCase):
    def test_symmetric_two_span_beam(self):
        """
        Symmetric 2-span beam under uniform load:
        Spans: 2, L = 6.0 m each, EI = 10000.0 kNm^2 each
        Supports: Pinned, Continuous, Pinned
        Loads: UDL of 10.0 kN/m on both spans.
        Theoretical results:
          Support moment at center: 45.0 kNm (hogging, i.e., M_R[0] = 45.0, M_L[1] = -45.0)
          Outer support moments: 0.0 kNm
          Outer reactions (0 and 2): 3/8 * w * L = 3/8 * 10 * 6 = 22.5 kN
          Center reaction (1): 5/4 * w * L = 1.25 * 10 * 6 = 75.0 kN
        """
        spans = [
            {
                'L': 6.0,
                'EI': 10000.0,
                'loads': [{'type': 'UDL', 'w': 10.0, 'a': 0.0, 'b': 6.0}]
            },
            {
                'L': 6.0,
                'EI': 10000.0,
                'loads': [{'type': 'UDL', 'w': 10.0, 'a': 0.0, 'b': 6.0}]
            }
        ]
        supports = ['Pinned', 'Continuous', 'Pinned']

        result = BeamSolver.solve(spans, supports)

        # Print result details for debugging
        print("\n=== Test Symmetric Two-Span Beam ===")
        print("M_L:", result['M_L'])
        print("M_R:", result['M_R'])
        print("Reactions:", result['support_reactions'])

        # Assertions
        # Outer moments should be zero (pinned supports)
        self.assertAlmostEqual(result['M_L'][0], 0.0, places=3)
        self.assertAlmostEqual(result['M_R'][1], 0.0, places=3)
        
        # Center support moment should be 45.0 kNm
        self.assertAlmostEqual(result['M_R'][0], 45.0, places=3)
        self.assertAlmostEqual(result['M_L'][1], -45.0, places=3)

        # Reactions
        self.assertAlmostEqual(result['support_reactions'][0], 22.5, places=3)
        self.assertAlmostEqual(result['support_reactions'][1], 75.0, places=3)
        self.assertAlmostEqual(result['support_reactions'][2], 22.5, places=3)

    def test_fixed_fixed_single_span_beam(self):
        """
        Single span beam fixed at both ends:
        Spans: 1, L = 8.0 m, EI = 20000.0 kNm^2
        Supports: Fixed, Fixed
        Loads: UDL of 12.0 kN/m.
        Theoretical results:
          Support moment at left: -64.0 kNm (M_L[0] = -64.0)
          Support moment at right: 64.0 kNm (M_R[0] = 64.0)
          Reactions: w * L / 2 = 12 * 8 / 2 = 48.0 kN each
        """
        spans = [
            {
                'L': 8.0,
                'EI': 20000.0,
                'loads': [{'type': 'UDL', 'w': 12.0, 'a': 0.0, 'b': 8.0}]
            }
        ]
        supports = ['Fixed', 'Fixed']

        result = BeamSolver.solve(spans, supports)

        print("\n=== Test Fixed-Fixed Single-Span Beam ===")
        print("M_L:", result['M_L'])
        print("M_R:", result['M_R'])
        print("Reactions:", result['support_reactions'])

        # Assertions
        self.assertAlmostEqual(result['M_L'][0], -64.0, places=3)
        self.assertAlmostEqual(result['M_R'][0], 64.0, places=3)

        self.assertAlmostEqual(result['support_reactions'][0], 48.0, places=3)
        self.assertAlmostEqual(result['support_reactions'][1], 48.0, places=3)

    def test_modified_stiffness_method_details(self):
        """
        Verify specific distribution factors and step logs under the Modified Stiffness Method.
        2-span symmetric beam: supports Pinned, Continuous, Pinned.
        With both outer supports pinned:
          - DFs at outer supports should be 0.0 (since they are released initially).
          - DFs at center support should be 0.5 and 0.5 (using 3EI/L for both spans).
          - 'Release Pinned Ends' step should be logged.
          - Iterations should converge immediately (0 cycles / steps log length of 2).
        """
        spans = [
            {
                'L': 6.0,
                'EI': 10000.0,
                'loads': [{'type': 'UDL', 'w': 10.0, 'a': 0.0, 'b': 6.0}]
            },
            {
                'L': 6.0,
                'EI': 10000.0,
                'loads': [{'type': 'UDL', 'w': 10.0, 'a': 0.0, 'b': 6.0}]
            }
        ]
        supports = ['Pinned', 'Continuous', 'Pinned']

        result = BeamSolver.solve(spans, supports)

        # Assert DFs
        self.assertEqual(result['DF_right'][0], 0.0)
        self.assertEqual(result['DF_left'][2], 0.0)
        self.assertAlmostEqual(result['DF_left'][1], 0.5, places=5)
        self.assertAlmostEqual(result['DF_right'][1], 0.5, places=5)

        # Assert steps log
        step_names = [step['Step'] for step in result['steps_log']]
        self.assertIn('Release Pinned Ends', step_names)
        self.assertEqual(step_names, ['Initial FEM', 'Release Pinned Ends'])

if __name__ == '__main__':
    unittest.main()
