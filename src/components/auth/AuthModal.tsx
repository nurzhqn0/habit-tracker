"use client";

import { Button, Dialog, Flex, Text, TextField } from "@radix-ui/themes";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../hooks/useAuth";

type AuthModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

function generateCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

export default function AuthModal({ open, onOpenChange }: AuthModalProps) {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sentCode, setSentCode] = useState("");
  const [step, setStep] = useState<"email" | "code">("email");
  const [errorMessage, setErrorMessage] = useState("");

  const canSendCode = useMemo(() => email.trim().length > 4 && email.includes("@"), [email]);

  useEffect(() => {
    if (!open) {
      setStep("email");
      setEmail("");
      setCode("");
      setSentCode("");
      setErrorMessage("");
    }
  }, [open]);

  const onSendCode = () => {
    if (!canSendCode) {
      setErrorMessage("Enter a valid email.");
      return;
    }

    const generated = generateCode();
    setSentCode(generated);
    setStep("code");
    setErrorMessage("");
  };

  const onVerify = () => {
    if (!code.trim()) {
      setErrorMessage("Enter the code.");
      return;
    }

    if (code.trim() !== sentCode) {
      setErrorMessage("Incorrect code. Try again.");
      return;
    }

    login(email);
    router.replace("/dashboard");
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Content maxWidth="420px">
        <Dialog.Title>Login to HabitFlow</Dialog.Title>
        <Dialog.Description size="2" mb="4">
          {step === "email" ? "Enter your email and we will send a code." : "Enter the code sent to your email."}
        </Dialog.Description>

        <Flex direction="column" gap="3">
          {step === "email" ? (
            <label className="grid gap-1">
              <Text size="2" weight="medium">
                Email
              </Text>
              <TextField.Root
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
          ) : (
            <>
              <Text size="2" color="gray">
                Code sent to <strong>{email}</strong>
              </Text>
              <label className="grid gap-1">
                <Text size="2" weight="medium">
                  Verification code
                </Text>
                <TextField.Root
                  type="text"
                  inputMode="numeric"
                  placeholder="6-digit code"
                  value={code}
                  onChange={(event) => setCode(event.target.value)}
                />
              </label>
              <Text size="2" color="amber">
                Demo mode: use code <strong>{sentCode}</strong>
              </Text>
            </>
          )}

          {errorMessage ? (
            <Text size="2" color="red">
              {errorMessage}
            </Text>
          ) : null}
        </Flex>

        <Flex gap="3" justify="end" mt="5">
          <Button variant="soft" color="gray" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          {step === "email" ? (
            <Button onClick={onSendCode}>Send code</Button>
          ) : (
            <Button onClick={onVerify}>Verify & login</Button>
          )}
        </Flex>
      </Dialog.Content>
    </Dialog.Root>
  );
}
