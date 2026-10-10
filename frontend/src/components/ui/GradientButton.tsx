import { chakra } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import type { ComponentProps } from 'react';

const MotionButton = motion.create(chakra.button);

type GradientButtonProps = ComponentProps<typeof MotionButton>;

export function GradientButton({ children, ...props }: GradientButtonProps) {
  return (
    <MotionButton
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      px={6}
      py={3}
      rounded="full"
      fontWeight="semibold"
      color="white"
      bgGradient="to-r"
      gradientFrom="purple.500"
      gradientTo="pink.500"
      cursor="pointer"
      _hover={{ shadow: 'lg' }}
      {...props}
    >
      {children}
    </MotionButton>
  );
}
