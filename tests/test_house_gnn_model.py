import importlib.util
import unittest


HAS_TORCH = importlib.util.find_spec("torch") is not None
HAS_PYG = importlib.util.find_spec("torch_geometric") is not None


@unittest.skipUnless(HAS_TORCH and HAS_PYG, "torch and torch_geometric are not installed")
class HouseGNNModelTests(unittest.TestCase):
    def test_forward_shapes(self):
        import torch

        from ml.house_service.gnn.model import HouseGNNResidualImputer

        model = HouseGNNResidualImputer(
            input_dim=6,
            edge_dim=7,
            numeric_imputation_dim=3,
            binary_imputation_dim=2,
            categorical_cardinalities=[4],
            hidden_dim=16,
            heads=4,
            dropout=0.0,
        )
        x = torch.randn(4, 6)
        edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
        edge_attr = torch.randn(4, 7)

        outputs = model(x, edge_index, edge_attr)

        self.assertEqual(outputs["residual_log_price"].shape, (4,))
        self.assertEqual(outputs["standalone_log_price"].shape, (4,))
        self.assertEqual(outputs["numeric_imputation"].shape, (4, 3))
        self.assertEqual(outputs["binary_imputation"].shape, (4, 2))
        self.assertEqual(outputs["categorical_imputation"][0].shape, (4, 4))


if __name__ == "__main__":
    unittest.main()
