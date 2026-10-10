import { SimpleGrid, Stat, Text } from '@chakra-ui/react';
import { GlassCard } from '../ui/GlassCard';
import type { AdminStatsData } from '../../types';

interface AdminStatsProps {
  stats: AdminStatsData;
}

export function AdminStats({ stats }: AdminStatsProps) {
  const items: { label: string; value: string; help?: string }[] = [
    { label: 'Total users', value: String(stats.total_users), help: `${stats.active_users} active` },
    { label: 'Total submissions', value: String(stats.total_submissions) },
    { label: 'Completed', value: String(stats.completed_submissions) },
    { label: 'Failed', value: String(stats.failed_submissions) },
    {
      label: 'Average score',
      value: stats.average_score === null ? 'N/A' : stats.average_score.toFixed(1),
    },
  ];

  return (
    <SimpleGrid columns={{ base: 1, sm: 2, lg: 3 }} gap={4}>
      {items.map((item) => (
        <GlassCard key={item.label}>
          <Stat.Root>
            <Stat.Label>{item.label}</Stat.Label>
            <Stat.ValueText fontSize="3xl">{item.value}</Stat.ValueText>
            {item.help ? (
              <Text color="fg.muted" fontSize="sm">
                {item.help}
              </Text>
            ) : null}
          </Stat.Root>
        </GlassCard>
      ))}
    </SimpleGrid>
  );
}
