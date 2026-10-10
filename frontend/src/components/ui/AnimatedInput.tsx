import { Box, Field, Input } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import type { ComponentProps } from 'react';

const MotionBox = motion.create(Box);

interface AnimatedInputProps extends ComponentProps<typeof Input> {
  label: string;
  error?: string;
}

export function AnimatedInput({ label, error, ...props }: AnimatedInputProps) {
  return (
    <Field.Root invalid={Boolean(error)}>
      <Field.Label>{label}</Field.Label>
      <MotionBox w="full" whileFocus={{ scale: 1.01 }} whileHover={{ y: -1 }}>
        <Input bg="whiteAlpha.700" rounded="xl" borderColor="gray.300" _focusVisible={{ borderColor: 'purple.500' }} {...props} />
      </MotionBox>
      {error ? <Field.ErrorText>{error}</Field.ErrorText> : null}
    </Field.Root>
  );
}
