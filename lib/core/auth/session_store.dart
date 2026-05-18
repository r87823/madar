abstract class SessionStore {
  String? get sid;

  Future<void> saveSid(String sid);

  Future<void> clear();
}

class MemorySessionStore implements SessionStore {
  MemorySessionStore({String? sid}) : _sid = sid;

  String? _sid;

  @override
  String? get sid => _sid;

  @override
  Future<void> saveSid(String sid) async {
    _sid = sid;
  }

  @override
  Future<void> clear() async {
    _sid = null;
  }
}
