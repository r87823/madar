import 'package:flutter/material.dart';

import 'madar_ui.dart';

class InfoSection extends StatelessWidget {
  const InfoSection({required this.title, required this.rows, super.key});

  final String title;
  final Map<String, String> rows;

  @override
  Widget build(BuildContext context) {
    return MadarInfoCard(title: title, rows: rows);
  }
}
