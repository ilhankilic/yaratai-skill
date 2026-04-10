# filepath: skills/css/var-extract/worker.py
import logging, re
from collections import Counter
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)|hsla?\([^)]+\)")
SIZE_RE = re.compile(r"\b\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw)\b")
NAMED_COLORS = {"#ff0000": "red", "#00ff00": "green", "#0000ff": "blue",
                "#ffffff": "white", "#000000": "black", "#fff": "white", "#000": "black"}

class Worker(BaseWorker):
    """Extract repeated CSS values into custom properties."""
    skill_id = "css.var-extract"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            css: str = input.data.get("css", "")
            if not css.strip():
                return SkillOutput(success=False, error="'css' is required.")
            min_occ: int = input.data.get("min_occurrences", 2)
            prefix: str = input.data.get("prefix", "--sf")
            cats: list = input.data.get("categories", ["color", "size"])

            values: list[str] = []
            if "color" in cats:
                values.extend(COLOR_RE.findall(css))
            if "size" in cats:
                values.extend(SIZE_RE.findall(css))

            counts = Counter(values)
            var_map: dict[str, str] = {}
            idx = {"color": 0, "size": 0}

            for val, cnt in counts.most_common():
                if cnt < min_occ:
                    continue
                lv = val.lower()
                if lv in NAMED_COLORS:
                    name = f"{prefix}-{NAMED_COLORS[lv]}"
                elif COLOR_RE.match(val):
                    idx["color"] += 1
                    name = f"{prefix}-color-{idx['color']}"
                else:
                    idx["size"] += 1
                    name = f"{prefix}-size-{idx['size']}"
                var_map[val] = name

            converted = css
            for val, name in var_map.items():
                converted = converted.replace(val, f"var({name})")

            var_block = ":root {\n" + "".join(f"  {name}: {val};\n" for val, name in var_map.items()) + "}\n"
            full = var_block + "\n" + converted

            return SkillOutput(success=True, data={
                "converted_css": converted, "variables_css": var_block,
                "full_css": full, "extracted_count": len(var_map), "variable_map": var_map,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
