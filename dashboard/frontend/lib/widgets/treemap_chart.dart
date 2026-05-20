import 'package:flutter/material.dart';
import 'package:syncfusion_flutter_treemap/treemap.dart';

import '../theme/app_colors.dart';

class CommunityTile {
  const CommunityTile({required this.label, required this.size, this.isNiche = false});
  final String label;
  final int size;
  final bool isNiche;
}

class TreemapChart extends StatelessWidget {
  const TreemapChart({super.key, required this.tiles});
  final List<CommunityTile> tiles;

  @override
  Widget build(BuildContext context) {
    final palette = [
      AppColors.emerald500,
      AppColors.emerald700,
      AppColors.emerald800,
      AppColors.emerald900,
    ];
    return SizedBox(
      height: 320,
      child: SfTreemap(
        dataCount: tiles.length,
        weightValueMapper: (i) => tiles[i].size.toDouble(),
        levels: [
          TreemapLevel(
            padding: const EdgeInsets.all(2),
            groupMapper: (i) => tiles[i].label,
            itemBuilder: (context, model) {
              final idx = tiles.indexWhere((t) => t.label == model.group);
              if (idx < 0) return const SizedBox.shrink();
              final t = tiles[idx];
              return Container(
                color: t.isNiche ? AppColors.graySlate : palette[idx % palette.length],
                padding: const EdgeInsets.all(10),
                alignment: Alignment.bottomLeft,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.end,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(t.label,
                        style: const TextStyle(color: Colors.white, fontSize: 11)),
                    Text('${t.size}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                        )),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
