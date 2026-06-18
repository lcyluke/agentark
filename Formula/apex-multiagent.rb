class ApexMultiagent < Formula
  include Language::Python::Virtualenv

  desc "⚡ Multi-Agent Operating System — one person, infinite capacity"
  homepage "https://github.com/lcyluke/apex"
  url "https://github.com/lcyluke/apex/archive/refs/tags/v0.3.0.tar.gz"
  sha256 "f941e0377c73cc25ffbc7c494406ec06323737f75264c40a24def43592ab9485"
  license "MIT"

  depends_on "python@3.12"
  depends_on "tmux"

  def install
    virtualenv_install_with_resources
  end

  def post_install
    # Print fleet quickstart
    ohai "🚀 Apex Fleet Quickstart"
    puts ""
    puts "  Initialize your fleet (one-time):"
    puts "    apex fleet init"
    puts ""
    puts "  Start all agents:"
    puts "    apex fleet start"
    puts ""
    puts "  Attach to your fleet:"
    puts "    apex fleet attach"
    puts ""
    puts "  Or manage individually:"
    puts "    apex fleet add <agent>    Add an agent"
    puts "    apex fleet log <agent>    View agent output"
    puts "    apex fleet broadcast \"msg\"  Send to all agents"
    puts "    apex fleet status          Fleet overview"
    puts ""
  end

  test do
    output = shell_output("#{bin}/apex --version 2>&1 || true")
    assert_match "Apex", output
  end

  def caveats
    <<~EOS
      ⚡ Apex installed with tmux multi-agent fleet.

      First run:
        apex fleet init    # Create profiles + start fleet (one-time)
        apex fleet start   # Launch all 7 dev agents in tmux windows
        apex fleet attach  # Show tmux attach command

      Fleet commands:
        apex fleet {init,start,stop,attach,add,kill,log,status,broadcast}

      Docs: https://github.com/lcyluke/apex
    EOS
  end
end
