import html
import re
from typing import Dict, Optional


class TemplateRenderer:
    @staticmethod
    def render(
        template_text: str,
        context: Dict[str, str]
    ) -> str:
        if not template_text:
            return ""

        rendered = template_text
        for key, val in context.items():
            escaped_key = re.escape(key)
            pattern = re.compile(r"\{\{\s*" + escaped_key + r"\s*\}\}", re.IGNORECASE)
            rendered = pattern.sub(str(val), rendered)

        # Fallback any unreplaced common variables
        rendered = re.sub(r"\{\{\s*first_name\s*\}\}", "there", rendered, flags=re.IGNORECASE)
        rendered = re.sub(r"\{\{\s*full_name\s*\}\}", "Collaborator", rendered, flags=re.IGNORECASE)
        rendered = re.sub(r"\{\{\s*project_name\s*\}\}", "your project", rendered, flags=re.IGNORECASE)

        return rendered

    @staticmethod
    def markdown_to_html(markdown_text: str) -> str:
        """Lightweight and safe markdown to HTML parser for outreach emails."""
        escaped = html.escape(markdown_text)

        # Bold: **text**
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

        # Italic: *text*
        escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)

        # Links: [text](url) - ensure only http/https links
        def link_repl(match):
            title = match.group(1)
            url = match.group(2)
            if url.startswith("http://") or url.startswith("https://") or url.startswith("mailto:"):
                return f'<a href="{url}" style="color: #6366f1; text-decoration: underline;">{title}</a>'
            return title

        escaped = re.sub(r"\[(.+?)\]\((.+?)\)", link_repl, escaped)

        # Paragraphs
        paragraphs = escaped.split("\n\n")
        html_paragraphs = [
            f"<p style='line-height: 1.6; margin-bottom: 14px;'>{p.replace(chr(10), '<br/>')}</p>"
            for p in paragraphs if p.strip()
        ]

        body = "\n".join(html_paragraphs)
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; background-color: #ffffff; padding: 20px;">
{body}
</body>
</html>"""
