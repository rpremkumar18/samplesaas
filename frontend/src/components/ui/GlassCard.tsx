import { Box, type BoxProps } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

const MotionBox = motion.create(Box);

interface GlassCardProps extends Omit<BoxProps, 'transition' | 'onAnimationStart' | 'onDrag' | 'onDragStart' | 'onDragEnd'> {
  children: ReactNode;
}

export function GlassCard({ children, ...rest }: GlassCardProps) {
  return (
    <MotionBox
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      p={6}
      rounded="2xl"
      bg={{ base: 'whiteAlpha.900', _dark: 'whiteAlpha.100' }}
      color="fg"
      backdropFilter="blur(16px)"
      borderWidth="1px"
      borderColor={{ base: 'blackAlpha.200', _dark: 'whiteAlpha.300' }}
      shadow="xl"
      {...rest}
    >
      {children}
    </MotionBox>
  );
}
