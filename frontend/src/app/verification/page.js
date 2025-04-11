"use client"

import { useState, useEffect, useMemo } from 'react'
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form"
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthProvider';
import { goToNextOnboardingStep } from "@/lib/utils"


const formSchema = z.object({
    verificationCode: z.string().min(6, { message: "Complete code is required." }),
})

// CountdownTimer component
const CountdownTimer = ({ initialTime, onExpire }) => {
    const [timeLeft, setTimeLeft] = useState(initialTime)

    useEffect(() => {
        if (timeLeft <= 0) {
            onExpire()
            return
        }

        const timer = setInterval(() => {
            setTimeLeft(prev => prev - 1)
        }, 1000)

        return () => clearInterval(timer)
    }, [timeLeft, onExpire])

    const minutes = Math.floor(timeLeft / 60)
    const seconds = timeLeft % 60

    return (
        <span className="text-sm text-athletic-charcoal/80">
            {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </span>
    )
}

// VerificationForm component
const VerificationForm = ({ onSubmit, onResend, isLoading }) => {
    const form = useForm({
        resolver: zodResolver(formSchema),
        defaultValues: {
            verificationCode: "",
        },
    })
    // const [code, setCode] = useState("")
    const [isTimerExpired, setIsTimerExpired] = useState(false)

    const handleSubmit = (formData) => {
        onSubmit(formData.verificationCode)
    }

    const handleTimerExpire = () => {
        setIsTimerExpired(true)
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
                <FormField
                    control={form.control}
                    name="verificationCode"
                    render={({ field }) => (
                        <FormItem className="flex flex-col items-start">
                            <FormControl className="w-full">
                                <div className="flex justify-center">
                                    <InputOTP
                                        maxLength={6}
                                        value={field.value}
                                        onChange={(value) => {
                                            form.setValue('verificationCode', value)
                                        }}
                                    >
                                        <InputOTPGroup>
                                            <InputOTPSlot index={0} className="h-12 w-12" />
                                            <InputOTPSlot index={1} className="h-12 w-12" />
                                            <InputOTPSlot index={2} className="h-12 w-12" />
                                            <InputOTPSlot index={3} className="h-12 w-12" />
                                            <InputOTPSlot index={4} className="h-12 w-12" />
                                            <InputOTPSlot index={5} className="h-12 w-12" />
                                        </InputOTPGroup>
                                    </InputOTP>
                                </div>
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <div className="text-center">
                    {!isTimerExpired && (
                        <p className="text-sm mb-4">
                            Code expires in <CountdownTimer initialTime={120} onExpire={handleTimerExpire} />
                        </p>
                    )}

                    <Button
                        type="submit"
                        className="w-full bg-[#0F213F] text-white py-3 rounded-md tracking-wider uppercase text-xs font-semibold hover:bg-[#333333] transition-all duration-300 ease-in-out transform hover:-translate-y-1"
                        disabled={isLoading || isTimerExpired}
                    >
                        Confirm
                    </Button>

                    <Button
                        type="button"
                        variant="ghost"
                        onClick={onResend}
                        className="text-athletic-navy/70 text-sm hover:text-athletic-navy transition-colors duration-300 mt-2"
                    >
                        Resend Code
                    </Button>
                </div>
            </form>
        </Form>
    )
}

const VerifyHeader = () => {
    const [phoneNumber, setPhoneNumber] = useState('')

    useEffect(() => {
        const storedPhoneNumber = localStorage.getItem("phoneNumber")
        setPhoneNumber(storedPhoneNumber)
    }, [])

    const formatPhoneNumber = (rawPhone) => {
        if (!rawPhone) return ''
        const digits = rawPhone.replace(/\D/g, '')
        let formatted = ''
        if (digits.length === 11 && digits.startsWith('1')) {
            formatted = digits.slice(1)
        } else if (digits.length === 10) {
            formatted = digits
        }

        if (formatted.length === 10) {
            return `+1 (${formatted.slice(0, 3)}) ${formatted.slice(3, 6)}-${formatted.slice(6)}`
        }

        // fallback to raw if unexpected format
        return rawPhone
    }

    const formattedPhoneNumber = useMemo(() => {
        if (!phoneNumber) return ''
        return formatPhoneNumber(phoneNumber)
    }, [phoneNumber])

    return (
        <div>
            <h1 className="font-cormorant text-3xl text-athletic-navy mb-6 text-center">Verify your number</h1>
            {formattedPhoneNumber && (
                <p className="text-sm text-athletic-charcoal/80 text-center mb-6">
                    We sent a code to <span className="font-semibold">{formattedPhoneNumber}</span>
                </p>
            )}
        </div>
    )
}

// Main VerificationPage component
const VerificationPage = () => {
    const [isLoading, setIsLoading] = useState(false)
    const { loginWithToken } = useAuth()
    const router = useRouter()
    const pathname = usePathname()

    const handleSubmit = async (code) => {
        if (isLoading) return
        setIsLoading(true)
        const phoneNumber = localStorage.getItem("phoneNumber")
        try {
            const res = await fetch(process.env.NEXT_PUBLIC_API_BASE_URL + "/api/v1/users/verify-code/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone_number: phoneNumber, verification_code: code })
            })
            const result = await res.json()
            if (res.ok) {
                toast("Success", { description: result.message || "Code verified successfully" })
                await loginWithToken(result.token)
                await goToNextOnboardingStep(router, pathname)
            } else {
                toast("Error", { description: result.error || "Verification failed" })
                setIsLoading(false)
            }
        } catch (error) {
            toast("Error", { description: "Unexpected error occurred." })
            setIsLoading(false)
        }
    }

    const handleResend = async () => {
        if (isLoading) return
        setIsLoading(true)
        const phoneNumber = localStorage.getItem("phoneNumber")
        try {
            const res = await fetch(process.env.NEXT_PUBLIC_API_BASE_URL + "/api/v1/users/verification-code/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone_number: phoneNumber })
            })
            const result = await res.json()
            if (res.ok) {
                toast("New Code Sent", { description: result.message || "A new verification code has been sent to your phone." })
                setIsLoading(false)
            } else {
                toast("Error", { description: result.error || "Failed to resend code" })
                setIsLoading(false)
            }
        } catch (error) {
            toast("Error", { description: "Unexpected error occurred." })
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-athletic-white flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <VerifyHeader />
                <div>
                    <VerificationForm
                        onSubmit={handleSubmit}
                        onResend={handleResend}
                        isLoading={isLoading}
                    />
                </div>
            </div>
        </div>
    )
}

export default VerificationPage