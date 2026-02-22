from __future__ import annotations

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context


def _build_templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory="app/templates")

    @pass_context
    def _relative_url_for(context, name: str, **path_params: str) -> str:
        request = context.get("request")
        if request is None:
            raise RuntimeError("request is required in template context")
        return str(request.app.url_path_for(name, **path_params))

    templates.env.globals["url_for"] = _relative_url_for
    return templates


templates = _build_templates()
