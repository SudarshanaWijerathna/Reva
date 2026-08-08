from typing import List


def require_torch_geometric():
    try:
        import torch
        from torch import nn
        from torch_geometric.nn import GATv2Conv
    except ImportError as exc:
        raise ImportError(
            "The house GNN requires torch and torch-geometric. "
            "Install the CPU-compatible packages before training or serving GNN artifacts."
        ) from exc
    return torch, nn, GATv2Conv


torch, nn, GATv2Conv = require_torch_geometric()


class HouseGNNResidualImputer(nn.Module):
    def __init__(
        self,
        input_dim: int,
        edge_dim: int,
        numeric_imputation_dim: int,
        binary_imputation_dim: int,
        categorical_cardinalities: List[int],
        hidden_dim: int = 64,
        heads: int = 4,
        dropout: float = 0.25,
    ) -> None:
        super().__init__()
        if hidden_dim % heads != 0:
            raise ValueError("hidden_dim must be divisible by heads")

        self.input_dim = input_dim
        self.edge_dim = edge_dim
        self.hidden_dim = hidden_dim
        self.heads = heads
        self.dropout = dropout
        self.categorical_cardinalities = categorical_cardinalities

        out_channels = hidden_dim // heads
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        self.gat1 = GATv2Conv(
            hidden_dim,
            out_channels,
            heads=heads,
            edge_dim=edge_dim,
            dropout=dropout,
            add_self_loops=False,
        )
        self.gat2 = GATv2Conv(
            hidden_dim,
            out_channels,
            heads=heads,
            edge_dim=edge_dim,
            dropout=dropout,
            add_self_loops=False,
        )
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.activation = nn.SiLU()
        self.dropout_layer = nn.Dropout(dropout)

        self.price_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
        )
        self.standalone_price_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
        )
        self.numeric_imputation_head = nn.Linear(hidden_dim, numeric_imputation_dim)
        self.binary_imputation_head = nn.Linear(hidden_dim, binary_imputation_dim)
        self.categorical_imputation_heads = nn.ModuleList(
            [nn.Linear(hidden_dim, cardinality) for cardinality in categorical_cardinalities]
        )

    def forward(self, x, edge_index, edge_attr):
        hidden = self.input_projection(x)
        hidden = self.norm1(hidden + self.dropout_layer(self.activation(self.gat1(hidden, edge_index, edge_attr))))
        hidden = self.norm2(hidden + self.dropout_layer(self.activation(self.gat2(hidden, edge_index, edge_attr))))

        return {
            "residual_log_price": self.price_head(hidden).squeeze(-1),
            "standalone_log_price": self.standalone_price_head(hidden).squeeze(-1),
            "numeric_imputation": self.numeric_imputation_head(hidden),
            "binary_imputation": self.binary_imputation_head(hidden),
            "categorical_imputation": [head(hidden) for head in self.categorical_imputation_heads],
            "embedding": hidden,
        }


def model_config_from_instance(model: HouseGNNResidualImputer) -> dict:
    return {
        "input_dim": model.input_dim,
        "edge_dim": model.edge_dim,
        "hidden_dim": model.hidden_dim,
        "heads": model.heads,
        "dropout": model.dropout,
        "categorical_cardinalities": model.categorical_cardinalities,
    }
