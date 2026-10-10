import { Box, Text } from '@chakra-ui/react';
import { motion } from 'framer-motion';

const MotionBox = motion.create(Box);

function scoreColor(score: number): string {
  if (score >= 75) return 'green.400';
  if (score >= 50) return 'yellow.400';
  if (score >= 30) return 'orange.400';
  return 'red.400';
}

interface ScoreBadgeProps {
  score: number;
  size?: 'sm' | 'lg';
}

export function ScoreBadge({ score, size = 'lg' }: ScoreBadgeProps) {
  const big = size === 'lg';
  const color = scoreColor(score);
  return (
    <MotionBox
      initial={{ scale: 0.5, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 12 }}
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      w={big ? '160px' : '56px'}
      h={big ? '160px' : '56px'}
      rounded="full"
      borderWidth={big ? '8px' : '3px'}
      borderColor={color}
      flexShrink={0}
      aria-label={`Score ${score} out of 100`}
    >
      <Text fontSize={big ? '5xl' : 'md'} fontWeight="extrabold" color={color} lineHeight="1">
        {score}
      </Text>
      {big && (
        <Text fontSize="sm" color="gray.400">
          / 100
        </Text>
      )}
    </MotionBox>
  );
}
