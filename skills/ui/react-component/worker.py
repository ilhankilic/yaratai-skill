# filepath: skills/ui/react-component/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

VARIANT_CLASSES = {
    "button": "inline-flex items-center justify-center rounded-md px-4 py-2 font-medium",
    "card": "rounded-lg border bg-white p-6 shadow-sm",
    "form": "space-y-4",
    "list": "divide-y divide-gray-200",
    "modal": "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
    "generic": "",
}

class Worker(BaseWorker):
    """Generate TypeScript React component."""
    skill_id = "ui.react-component"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            name: str = input.data.get("component_name", "")
            if not name:
                return SkillOutput(success=False, error="'component_name' is required.")

            desc: str = input.data.get("description", f"A {name} component.")
            props: list = input.data.get("props", [])
            variant: str = input.data.get("variant", "generic")
            storybook: bool = input.data.get("with_storybook", False)

            if variant not in VARIANT_CLASSES:
                return SkillOutput(success=False, error=f"Unknown variant '{variant}'. Use: {list(VARIANT_CLASSES)}")

            # Props interface
            iface_lines = [f"export interface {name}Props {{"]
            for p in props:
                req = "" if p.get("required", True) else "?"
                iface_lines.append(f"  /** {p.get('description', '')} */")
                iface_lines.append(f"  {p['name']}{req}: {p.get('type', 'string')};")
            iface_lines.append("}")

            # Destructure
            destructure = ", ".join(p["name"] for p in props) if props else ""
            defaults = []
            for p in props:
                if "default" in p:
                    defaults.append(f"{p['name']} = {repr(p['default'])}")
                else:
                    defaults.append(p["name"])

            has_state = variant in ("form", "modal")
            state_line = '  const [open, setOpen] = useState(false);' if has_state else ""
            import_line = "import React, { useState } from 'react';" if has_state else "import React from 'react';"

            tw = VARIANT_CLASSES[variant]
            body = f'    <div className="{tw}">\n      {{/* {desc} */}}\n    </div>'

            comp = f"""{import_line}

{chr(10).join(iface_lines)}

/**
 * {desc}
 */
export default function {name}({{ {', '.join(defaults)} }}: {name}Props) {{
{state_line}
  return (
{body}
  );
}}
"""
            story = ""
            if storybook:
                story = f"""import type {{ Meta, StoryObj }} from '@storybook/react';
import {name} from './{name}';

const meta: Meta<typeof {name}> = {{ component: {name}, title: '{name}' }};
export default meta;
type Story = StoryObj<typeof {name}>;

export const Default: Story = {{ args: {{}} }};
"""

            return SkillOutput(success=True, data={
                "component_code": comp, "story_code": story,
                "prop_count": len(props), "has_state": has_state,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
