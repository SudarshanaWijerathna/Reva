import unittest

import numpy as np
import pandas as pd

from ml.house_service.gnn.graph_builder import (
    GraphBuildConfig,
    build_property_graph,
    edge_leakage_count,
)
from ml.house_service.gnn.schema import EDGE_ATTR_COLUMNS


class HouseGNNGraphTests(unittest.TestCase):
    def _frame(self):
        return pd.DataFrame(
            {
                "lat": [6.9, 6.9, 6.91, 7.0, 7.01],
                "lon": [79.9, 79.9, 79.91, 80.0, 80.01],
                "district": ["colombo", "colombo", "colombo", "gampaha", "gampaha"],
                "sub_location": ["a", "a", "b", "c", "c"],
                "house_quality_tier": ["normal", "normal", "luxury", "normal", "normal"],
                "posted_year": [2023, 2023, 2024, 2025, 2025],
                "posted_month": [1, 2, 3, 4, 5],
            }
        )

    def test_graph_caps_edges_and_aligns_edge_attributes(self):
        frame = self._frame()
        features = np.asarray(
            [
                [1.0, 0.0, 0.0],
                [1.0, 0.1, 0.0],
                [0.8, 0.2, 0.0],
                [0.0, 1.0, 1.0],
                [0.0, 0.9, 1.0],
            ],
            dtype=np.float32,
        )
        graph = build_property_graph(
            frame,
            features,
            GraphBuildConfig(spatial_k=2, feature_k=2, location_k=1),
        )

        self.assertEqual(graph.edge_index.shape[0], 2)
        self.assertEqual(graph.edge_attr.shape[0], graph.edge_index.shape[1])
        self.assertEqual(graph.edge_attr.shape[1], len(EDGE_ATTR_COLUMNS))
        self.assertLessEqual(graph.edge_index.shape[1], len(frame) * (2 + 2 + 1) * 2)

    def test_train_validation_leakage_count_detects_cross_edges(self):
        edge_index = np.asarray([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=np.int64)
        train_mask = np.asarray([True, True, False, False])
        validation_mask = ~train_mask

        self.assertEqual(edge_leakage_count(edge_index, train_mask, validation_mask), 2)

    def test_isolated_single_node_gets_self_loop(self):
        frame = self._frame().iloc[:1].copy()
        graph = build_property_graph(frame, np.asarray([[1.0, 2.0]], dtype=np.float32))

        self.assertEqual(graph.edge_index.shape, (2, 1))
        self.assertEqual(graph.edge_index[0, 0], 0)
        self.assertEqual(graph.edge_index[1, 0], 0)


if __name__ == "__main__":
    unittest.main()
