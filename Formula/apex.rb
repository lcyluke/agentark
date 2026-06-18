class Apex < Formula
  include Language::Python::Virtualenv

  desc "⚡ Multi-Agent Operating System — one person, infinite capacity"
  homepage "https://github.com/lcyluke/apex"
  url "https://github.com/lcyluke/apex/archive/refs/tags/v0.3.2.tar.gz"
  sha256 "1095ebc57f814198146540580a78d1a1393aa91115a0e3023ed77be3461d2cc7"
  license "MIT"

  depends_on "python@3.12"
  depends_on "tmux"

  def install
    virtualenv_install_with_resources
  end

  def post_install
    ohai "🚀 Apex Fleet Quickstart"
    puts ""
    puts "  Initialize your fleet (one-time):"
    puts "    apex fleet init"
    puts ""
    puts "  Start all agents:"
    puts "    apex fleet start"
    puts ""
    puts "  Monitor your fleet:"
    puts "    apex monitor status"
    puts "    apex monitor skills"
    puts ""
    puts "Docs: https://github.com/lcyluke/apex"
    puts ""
  end

  test do
    output = shell_output("#{bin}/apex --version 2>&1 || true")
    assert_match "Apex", output
  end

  def caveats
    <<~EOS
      ⚡ Apex — Multi-Agent Operating System

      Quickstart:
        apex fleet init      Create profiles + launch fleet (one-time)
        apex fleet start     Start 7 dev agents in tmux windows
        apex monitor status  Agent status + badminton pipeline

      Fleet commands:
        apex fleet {init,start,stop,attach,add,kill,log,status,broadcast}
      Monitor commands:
        apex monitor {status,skills}

      Works on macOS, Linux, and Windows (WSL).

      Docs: https://github.com/lcyluke/apex
    EOS
  end
end
