from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from .models import GeneratorConfig, LAYOUTS, SCENARIOS


class ConfigError(ValueError):
    pass


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small config/default.yaml shape without external dependencies."""
    result: dict[str, Any] = {}
    current_section: str | None = None
    current_list_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and stripped.endswith(":"):
            current_section = stripped[:-1]
            result[current_section] = {}
            current_list_key = None
            continue
        if current_section is None:
            continue
        section = result[current_section]
        if stripped.startswith("- "):
            if current_list_key is None:
                raise ConfigError(f"List item without key in {path}: {raw_line}")
            section[current_list_key].append(_parse_scalar(stripped[2:]))
            continue
        if ":" in stripped:
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            if raw_value == "":
                section[key] = []
                current_list_key = key
            else:
                section[key] = _parse_scalar(raw_value)
                current_list_key = None
    return result


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")


def load_config(path: str | None = None) -> GeneratorConfig:
    config = GeneratorConfig()
    if not path:
        return config

    raw = parse_simple_yaml(Path(path))
    dataset = raw.get("dataset", {})
    master_data = raw.get("master_data", {})
    invoice = raw.get("invoice", {})
    scenarios = raw.get("scenarios", {})
    rendering = raw.get("rendering", {})

    return replace(
        config,
        dataset_name=dataset.get("name", config.dataset_name),
        pdf_count=dataset.get("pdf_count", config.pdf_count),
        output_directory=dataset.get("output_directory", config.output_directory),
        seed=dataset.get("seed", config.seed),
        locale=master_data.get("locale", config.locale),
        currency=master_data.get("currency", config.currency),
        vendor_count=master_data.get("vendor_count", config.vendor_count),
        item_count=master_data.get("item_count", config.item_count),
        min_line_items=invoice.get("min_line_items", config.min_line_items),
        max_line_items=invoice.get("max_line_items", config.max_line_items),
        layouts=tuple(invoice.get("layouts", config.layouts)),
        scenario_weights=scenarios or config.scenario_weights,
        add_noise=rendering.get("add_noise", config.add_noise),
        add_rotation=rendering.get("add_rotation", config.add_rotation),
        render_po_pdfs=rendering.get("render_po_pdfs", config.render_po_pdfs),
        render_grn_pdfs=rendering.get("render_grn_pdfs", config.render_grn_pdfs),
    )


def apply_overrides(
    config: GeneratorConfig,
    pdf_count: int | None = None,
    seed: int | None = None,
    output: str | None = None,
    layouts: str | None = None,
    scenarios: list[str] | None = None,
    render_po_pdfs: bool = False,
    render_grn_pdfs: bool = False,
) -> GeneratorConfig:
    updates: dict[str, Any] = {}
    if pdf_count is not None:
        updates["pdf_count"] = pdf_count
    if seed is not None:
        updates["seed"] = seed
    if output is not None:
        updates["output_directory"] = output
    if layouts:
        updates["layouts"] = tuple(part.strip().upper() for part in layouts.split(",") if part.strip())
    if scenarios:
        weights: dict[str, float] = {}
        for item in scenarios:
            if "=" not in item:
                raise ConfigError(f"Scenario override must look like NAME=WEIGHT: {item}")
            name, value = item.split("=", 1)
            weights[name.strip().upper()] = float(value)
        updates["scenario_weights"] = weights
    if render_po_pdfs:
        updates["render_po_pdfs"] = True
    if render_grn_pdfs:
        updates["render_grn_pdfs"] = True
    return replace(config, **updates)


def validate_config(config: GeneratorConfig) -> None:
    if not isinstance(config.pdf_count, int):
        raise ConfigError("pdf_count must be an integer")
    if config.pdf_count <= 0:
        raise ConfigError("pdf_count must be greater than zero")
    if config.vendor_count <= 0:
        raise ConfigError("vendor_count must be greater than zero")
    if config.item_count <= 0:
        raise ConfigError("item_count must be greater than zero")
    if config.min_line_items <= 0:
        raise ConfigError("min_line_items must be greater than zero")
    if config.min_line_items > config.max_line_items:
        raise ConfigError("min_line_items cannot exceed max_line_items")

    invalid_layouts = sorted(set(config.layouts) - set(LAYOUTS))
    if invalid_layouts:
        raise ConfigError(f"Unsupported layouts: {', '.join(invalid_layouts)}")

    invalid_scenarios = sorted(set(config.scenario_weights) - set(SCENARIOS))
    if invalid_scenarios:
        raise ConfigError(f"Unsupported scenarios: {', '.join(invalid_scenarios)}")

    total_weight = sum(config.scenario_weights.values())
    if abs(total_weight - 1.0) > 0.000001:
        raise ConfigError(f"Scenario weights must sum to 1.0, got {total_weight:.6f}")


def config_to_dict(config: GeneratorConfig) -> dict[str, Any]:
    return {
        "dataset": {
            "name": config.dataset_name,
            "pdf_count": config.pdf_count,
            "output_directory": config.output_directory,
            "seed": config.seed,
        },
        "master_data": {
            "locale": config.locale,
            "currency": config.currency,
            "vendor_count": config.vendor_count,
            "item_count": config.item_count,
        },
        "invoice": {
            "min_line_items": config.min_line_items,
            "max_line_items": config.max_line_items,
            "layouts": list(config.layouts),
        },
        "scenarios": config.scenario_weights,
        "rendering": {
            "add_noise": config.add_noise,
            "add_rotation": config.add_rotation,
            "render_po_pdfs": config.render_po_pdfs,
            "render_grn_pdfs": config.render_grn_pdfs,
        },
    }


def dump_yaml_like(path: Path, value: dict[str, Any]) -> None:
    lines: list[str] = []
    for section, entries in value.items():
        lines.append(f"{section}:")
        for key, item in entries.items():
            if isinstance(item, list):
                lines.append(f"  {key}:")
                for list_item in item:
                    lines.append(f"    - {list_item}")
            else:
                rendered = str(item).lower() if isinstance(item, bool) else item
                lines.append(f"  {key}: {rendered}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
