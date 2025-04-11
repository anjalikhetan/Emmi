"use client"

import withAuth from '@/hoc/withAuth'
import { useEffect } from 'react'
import useConfetti from '@/hooks/useConfetti'

// Success Animation Component
const SuccessAnimation = () => (
    <div className="w-24 h-24 rounded-full bg-[#C0D9C5] flex items-center justify-center animate-[fadeIn_1.5s_ease-in-out_forwards]">
        <svg className="w-12 h-12 text-white animate-[checkmark_0.5s_ease-in-out_0.7s_forwards] opacity-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
    </div>
)

// Main Onboarding Confirmation Component
const OnboardingConfirmation = () => {
    useConfetti(true)
    return (
        <div className="min-h-screen bg-white flex items-center justify-center p-4">
            <div className="max-w-md w-full mx-auto rounded-3xl p-8 relative overflow-hidden">
                <div>
                    {/* Success Animation */}
                    <div className="mb-8 relative h-32 flex items-center justify-center">
                        <SuccessAnimation />
                    </div>

                    {/* Main Content */}
                    <div className="text-center space-y-6">
                        <h1 className="font-cormorant text-3xl md:text-4xl lg:text-5xl text-[#0F213F]">You&apos;re all set!</h1>
                        <p className="text-base md:text-lg lg:text-xl text-[#333333]/80">
                            I&apos;m crafting your personalized training plan based on your goals and background.
                        </p>
                        <p className="text-base md:text-lg lg:text-xl text-[#333333]/80">
                            I&apos;ll text you when it’s ready!
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default withAuth(OnboardingConfirmation)
