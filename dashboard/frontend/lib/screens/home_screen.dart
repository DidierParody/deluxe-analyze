import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../theme/app_colors.dart';
import '../widgets/feature_card.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: SafeArea(
        child: Container(
          decoration: const BoxDecoration(gradient: AppColors.pageGradient),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
            children: [
              const Text('👋 Hola',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
              const SizedBox(height: 4),
              const Text('Insights de Ventas',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              const Text('Análisis de tu red de clientes',
                  style: TextStyle(color: AppColors.textFaint, fontSize: 12)),
              const SizedBox(height: 24),
              FeatureCard(
                hero: true,
                icon: '🚀',
                title: '¿A cuántos llega una promoción?',
                description: 'Elige un cliente y mira hasta dónde llega su red social',
                onTap: () => context.push('/promo-reach'),
              ),
              const SizedBox(height: 12),
              FeatureCard(
                icon: '👑',
                iconBg: AppColors.emerald400.withOpacity(0.10),
                iconColor: AppColors.emerald300,
                title: 'Top clientes más influyentes',
                description: 'Los que más arrastran a otros a venir',
                onTap: () => context.push('/influencers'),
              ),
              const SizedBox(height: 12),
              FeatureCard(
                icon: '🎯',
                iconBg: AppColors.grayDark.withOpacity(0.18),
                iconColor: AppColors.grayLight,
                title: '¿A qué evento invito al cliente X?',
                description: 'Recomendaciones según sus amigos',
                onTap: () => context.push('/events'),
              ),
              const SizedBox(height: 12),
              FeatureCard(
                icon: '👥',
                iconBg: AppColors.emerald600.withOpacity(0.14),
                iconColor: AppColors.emerald400,
                title: 'Grupos sociales de tus clientes',
                description: 'Quiénes se mueven juntos',
                onTap: () => context.push('/communities'),
              ),
              const SizedBox(height: 12),
              FeatureCard(
                icon: '🌉',
                iconBg: AppColors.graySlate.withOpacity(0.20),
                iconColor: AppColors.grayMid,
                title: 'Brokers sociales',
                description: 'Clientes que conectan grupos distintos',
                onTap: () => context.push('/brokers'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
