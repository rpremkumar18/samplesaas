import { Box } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

const MotionBox = motion.create(Box);

const container = { hidden: {}, visible: { transition: { staggerChildren: 0.1 } } };
const item = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

export function AnimatedList({ children }: { children: ReactNode[] }) {
  return (
    <MotionBox initial="hidden" animate="visible" variants={container}>
      {children.map((child, i) => (
        <MotionBox key={i} variants={item}>
          {child}
        </MotionBox>
      ))}
    </MotionBox>
  );
}
