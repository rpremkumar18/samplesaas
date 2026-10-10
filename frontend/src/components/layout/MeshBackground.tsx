import { Box } from '@chakra-ui/react';

export function MeshBackground() {
  return (
    <Box position="fixed" inset={0} zIndex={-1} overflow="hidden" bg="bg">
      <Box
        position="absolute"
        top={0}
        left="25%"
        w="24rem"
        h="24rem"
        bg={{ base: 'purple.200', _dark: 'purple.700' }}
        rounded="full"
        filter="blur(80px)"
        opacity={0.4}
      />
      <Box
        position="absolute"
        bottom={0}
        right="25%"
        w="24rem"
        h="24rem"
        bg={{ base: 'pink.200', _dark: 'pink.700' }}
        rounded="full"
        filter="blur(80px)"
        opacity={0.4}
      />
    </Box>
  );
}
