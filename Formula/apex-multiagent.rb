class ApexMultiagent < Formula
  include Language::Python::Virtualenv

  desc "⚡ Multi-Agent Operating System — one person, infinite capacity"
  homepage "https://github.com/lcyluke/apex"
  url "https://github.com/lcyluke/apex/archive/refs/tags/v0.2.1.tar.gz"
  sha256 "e210d80e2fa7f7fb8a513c434eac1825c3e427ddaf2532e5cbf4dcc09e8f4d8f"
  license "MIT"

  depends_on "python@3.12"

  # Declared in pyproject.toml
  # click, httpx, pyyaml, pydantic, rich, jinja2

  def install
    virtualenv_install_with_resources
  end

  test do
    # Verify CLI entry point exists and runs
    output = shell_output("#{bin}/apex --version 2>&1 || true")
    assert_match "Apex", output
  end

  def caveats
    <<~EOS
      🚀 Apex installed! Get started:

        apex init my-project && cd my-project
        apex run "Write a login page"

      Multi-agent fleet mode:
        apex fleet status
        apex squad start

      Docs: https://github.com/lcyluke/apex
    EOS
  end
end
