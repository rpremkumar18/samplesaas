import { Box } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

const MotionBox = motion.create(Box);

export function PageWrapper({ children }: { children: ReactNode }) {
  return (
    <MotionBox
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.3 }}
      minH="100vh"
      p={8}
    >
      {children}
    </MotionBox>
  );
}
