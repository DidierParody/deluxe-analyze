import 'package:flutter/material.dart';

import '../api/dashboard_api.dart';
import '../models/user_summary.dart';
import '../theme/app_colors.dart';

class UserPicker extends StatefulWidget {
  const UserPicker({super.key, required this.selected, required this.onChanged});

  final UserSummary? selected;
  final ValueChanged<UserSummary> onChanged;

  @override
  State<UserPicker> createState() => _UserPickerState();
}

class _UserPickerState extends State<UserPicker> {
  @override
  Widget build(BuildContext context) {
    final u = widget.selected;
    return InkWell(
      onTap: _open,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withOpacity(0.08)),
        ),
        child: Row(
          children: [
            Container(
              width: 32, height: 32,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                gradient: AppColors.heroGradient,
                shape: BoxShape.circle,
              ),
              child: Text(
                u?.initial ?? '?',
                style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('CLIENTE', style: TextStyle(color: AppColors.textMuted, fontSize: 10, letterSpacing: 0.5)),
                  Text(
                    u == null ? 'Selecciona un cliente' : '${u.displayName} · ${u.id}',
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                  ),
                ],
              ),
            ),
            const Icon(Icons.expand_more, color: AppColors.textFaint),
          ],
        ),
      ),
    );
  }

  Future<void> _open() async {
    final result = await showModalBottomSheet<UserSummary>(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      builder: (_) => const _UserPickerSheet(),
    );
    if (result != null) widget.onChanged(result);
  }
}

class _UserPickerSheet extends StatefulWidget {
  const _UserPickerSheet();
  @override
  State<_UserPickerSheet> createState() => _UserPickerSheetState();
}

class _UserPickerSheetState extends State<_UserPickerSheet> {
  late Future<List<UserSummary>> _future;
  String _query = '';

  @override
  void initState() {
    super.initState();
    _future = DashboardApi().users(limit: 500);
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.7,
      builder: (_, ctrl) => Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              autofocus: true,
              decoration: InputDecoration(
                hintText: 'Buscar cliente…',
                prefixIcon: const Icon(Icons.search),
                filled: true,
                fillColor: Colors.white.withOpacity(0.04),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
              onChanged: (v) => setState(() => _query = v.toLowerCase()),
            ),
          ),
          Expanded(
            child: FutureBuilder<List<UserSummary>>(
              future: _future,
              builder: (_, snap) {
                if (!snap.hasData) return const Center(child: CircularProgressIndicator());
                final users = snap.data!.where((u) {
                  if (_query.isEmpty) return true;
                  return u.id.toLowerCase().contains(_query) ||
                      (u.username?.toLowerCase().contains(_query) ?? false);
                }).toList();
                return ListView.builder(
                  controller: ctrl,
                  itemCount: users.length,
                  itemBuilder: (_, i) {
                    final u = users[i];
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: AppColors.emerald700,
                        child: Text(u.initial, style: const TextStyle(color: Colors.white)),
                      ),
                      title: Text(u.displayName),
                      subtitle: Text(u.id, style: const TextStyle(fontSize: 11)),
                      onTap: () => Navigator.pop(context, u),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
