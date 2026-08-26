import { useState, useCallback, useRef } from 'react';

interface UseClipboardReturn {
  copyToClipboard: (text: string) => Promise<boolean>;
  copied: boolean;
}

export function useClipboard(): UseClipboardReturn {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const copyToClipboard = useCallback(
    async (text: string): Promise<boolean> => {
      // Clear any existing reset timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }

      try {
        // Primary: use the Clipboard API
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          timeoutRef.current = setTimeout(() => setCopied(false), 2000);
          return true;
        }

        // Fallback: use execCommand('copy')
        return fallbackCopy(text);
      } catch {
        // If Clipboard API fails, try fallback
        try {
          return fallbackCopy(text);
        } catch {
          setCopied(false);
          return false;
        }
      }
    },
    [],
  );

  function fallbackCopy(text: string): boolean {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    textarea.style.top = '-9999px';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    try {
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);
      if (success) {
        setCopied(true);
        timeoutRef.current = setTimeout(() => setCopied(false), 2000);
      }
      return success;
    } catch {
      document.body.removeChild(textarea);
      setCopied(false);
      return false;
    }
  }

  return { copyToClipboard, copied };
}
