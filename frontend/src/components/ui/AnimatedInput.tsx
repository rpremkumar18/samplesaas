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
      <MotionBox w="full" whileHover={{ y: -1 }}>
        <Input
          bg={{ base: 'white', _dark: 'whiteAlpha.100' }}
          color="fg"
          rounded="xl"
          borderColor="border.emphasized"
          _placeholder={{ color: 'fg.subtle' }}
          _focusVisible={{ borderColor: 'purple.500' }}
          {...props}
        />
      </MotionBox>
      {error ? <Field.ErrorText>{error}</Field.ErrorText> : null}
    </Field.Root>
  );
}
