from backend.campaigns.renderer import TemplateRenderer


def test_template_renderer_interpolation():
    template = "Hi {{first_name}},\n\nI saw {{project_name}} by {{organization_name}}."
    context = {
        "first_name": "Jordan",
        "project_name": "DistributedMesh",
        "organization_name": "TechNexus"
    }

    result = TemplateRenderer.render(template, context)
    assert "Hi Jordan," in result
    assert "I saw DistributedMesh by TechNexus." in result


def test_template_renderer_defaults():
    template = "Hi {{first_name}}, collaborating on {{project_name}}."
    result = TemplateRenderer.render(template, {})
    assert "Hi there," in result
    assert "collaborating on your project." in result


def test_markdown_to_html_formatting():
    markdown = "Hello **world**! Visit [our site](https://mailradar.dev).\n\nSecond paragraph."
    html_output = TemplateRenderer.markdown_to_html(markdown)

    assert "<strong>world</strong>" in html_output
    assert '<a href="https://mailradar.dev"' in html_output
    assert "<p style=" in html_output
