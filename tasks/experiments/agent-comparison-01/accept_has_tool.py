"""External checks for a requested feature in public SDK code, not an upstream defect."""
import inspect
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.tools.tool_manager import ToolManager


def test_manager_has_tool_is_exact_and_nonmutating():
    manager=ToolManager()
    assert manager.has_tool('missing') is False
    def ping(): return 'pong'
    manager.add_tool(ping)
    assert manager.has_tool('ping') is True
    assert manager.has_tool('Ping') is False
    assert manager.has_tool('') is False
    before=manager.list_tools()
    assert manager.has_tool('ping') is True
    assert manager.list_tools()==before
    manager.remove_tool('ping')
    assert manager.has_tool('ping') is False


def test_server_has_tool_delegates_without_running_tools(monkeypatch):
    server=MCPServer('Has tool pilot')
    def dangerous(): raise AssertionError('Lookup must not invoke a registered tool')
    assert server.has_tool('dangerous') is False
    server.add_tool(dangerous)
    assert server.has_tool('dangerous') is True
    assert server.has_tool('Dangerous') is False
    server.remove_tool('dangerous')
    assert server.has_tool('dangerous') is False
    assert not inspect.iscoroutinefunction(server.has_tool)
    calls=[]
    def lookup(name): calls.append(name); return name=='delegated'
    monkeypatch.setattr(server._tool_manager,'has_tool',lookup)
    assert server.has_tool('delegated') is True
    assert server.has_tool('other') is False
    assert calls==['delegated','other']
