class Agentark < Formula
  include Language::Python::Virtualenv

  desc "⚡ AgentArk — Multi-Agent Operating System. One person, infinite capacity."
  homepage "https://github.com/lcyluke/agentark"
  url "https://github.com/lcyluke/agentark/archive/refs/tags/v0.5.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"  # Run: curl -sL URL | shasum -a 256
  license "MIT"

  depends_on "python@3.12"
  depends_on "tmux"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    system libexec/"bin/pip", "install", "--upgrade", "pip"
    system libexec/"bin/pip", "install", "--only-binary", ":all:", "."
  end

  def post_install
    ohai "⚓ AgentArk Fleet Quickstart"
    puts ""
    puts "  Initialize your fleet (one-time):"
    puts "    agentark fleet init"
    puts ""
    puts "  Start all agents:"
    puts "    agentark fleet start"
    puts ""
    puts "  Monitor your fleet:"
    puts "    agentark fleet status"
    puts "    agentark fleet probe"
    puts ""
    puts "  LAN discovery:"
    puts "    agentark fleet lan scan"
    puts "    agentark fleet lan discover"
    puts ""
    puts "  Resource-aware dispatch:"
    puts "    agentark fleet dispatch \"task\" --gpu"
    puts ""
    puts "Docs: https://github.com/lcyluke/agentark"
    puts ""
  end

  test do
    output = shell_output("#{bin}/agentark --version 2>&1 || true")
    assert_match "AgentArk", output
  end

  def caveats
    <<~EOS
      ⚓ AgentArk — Multi-Agent Operating System
      46 agents, 30 commands, one CLI.

      Quickstart:
        agentark fleet init          Create profiles + launch fleet
        agentark fleet lan discover  Find other Macs on LAN
        agentark fleet dispatch -h   Resource-aware task dispatch

      Docs: https://github.com/lcyluke/agentark
    EOS
  end
end
