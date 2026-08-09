from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class LossWeights:
    price: float = 0.7
    imputation: float = 0.3
    standalone_price: float = 0.0


def require_torch():
    try:
        import torch
        import torch.nn.functional as functional
    except ImportError as exc:
        raise ImportError("The house GNN losses require torch.") from exc
    return torch, functional


torch, F = require_torch()


def multitask_loss(
    outputs: Dict[str, object],
    residual_target,
    standalone_target,
    numeric_target,
    binary_target,
    categorical_target,
    imputation_mask,
    weights: LossWeights,
) -> Dict[str, object]:
    price_loss = F.huber_loss(outputs["residual_log_price"], residual_target)
    standalone_loss = F.huber_loss(outputs["standalone_log_price"], standalone_target)

    numeric_loss = masked_mse(outputs["numeric_imputation"], numeric_target, imputation_mask["numeric"])
    binary_loss = masked_bce(outputs["binary_imputation"], binary_target, imputation_mask["binary"])
    categorical_loss = categorical_imputation_loss(
        outputs["categorical_imputation"],
        categorical_target,
        imputation_mask["categorical"],
    )
    imputation_loss = numeric_loss + binary_loss + categorical_loss
    total = (
        weights.price * price_loss
        + weights.imputation * imputation_loss
        + weights.standalone_price * standalone_loss
    )
    return {
        "total": total,
        "price": price_loss.detach(),
        "standalone_price": standalone_loss.detach(),
        "imputation": imputation_loss.detach(),
        "numeric_imputation": numeric_loss.detach(),
        "binary_imputation": binary_loss.detach(),
        "categorical_imputation": categorical_loss.detach(),
    }


def masked_mse(prediction, target, mask):
    if mask.numel() == 0 or mask.sum() <= 0:
        return prediction.sum() * 0.0
    return (((prediction - target) ** 2) * mask).sum() / mask.sum().clamp_min(1.0)


def masked_bce(logits, target, mask):
    if mask.numel() == 0 or mask.sum() <= 0:
        return logits.sum() * 0.0
    loss = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
    return (loss * mask).sum() / mask.sum().clamp_min(1.0)


def categorical_imputation_loss(logits_list: List[object], target, mask):
    if not logits_list:
        return target.sum() * 0.0

    losses = []
    for index, logits in enumerate(logits_list):
        column_mask = mask[:, index].bool()
        if column_mask.sum() <= 0:
            continue
        losses.append(F.cross_entropy(logits[column_mask], target[column_mask, index]))

    if not losses:
        return target.sum() * 0.0
    return torch.stack(losses).mean()
