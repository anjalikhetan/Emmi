"use client"

import React, { useState, useEffect } from 'react'
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { CheckCircle, UserRoundPen, XCircle, Check } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { cn } from '@/lib/utils'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '@/context/AuthProvider'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'
import { useMixpanel } from "@/context/MixpanelProvider";
import useConfetti from '@/hooks/useConfetti'


// CompletionStatus component
const CompletionStatus = ({ value, onChange }) => (
    <div className="space-y-4 mb-8">
        <h3 className="font-normal mb-4">How&apos;d it go?</h3>
        <RadioGroup value={value} onValueChange={onChange}>
            <div className="space-y-3">
                {[
                    { value: "completed", icon: CheckCircle, label: "Completed as planned" },
                    { value: "modified", icon: UserRoundPen, label: "Modified" },
                    { value: "skipped", icon: XCircle, label: "Skipped" }
                ].map((item) => (
                    <label
                        key={item.value}
                        className={cn(
                            "flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-colors text-sm",
                            value === item.value
                                ? "bg-[#0F213F] text-white"
                                : "text-gray-700 border-gray-200 border-2 hover:bg-[#0F213F]/5",
                        )}
                    >
                        <RadioGroupItem value={item.value} id={item.value} className="hidden" />
                        <item.icon className="w-5 h-5" />
                        <span className="">{item.label}</span>
                    </label>
                ))}
            </div>
        </RadioGroup>
    </div>
)


// DifficultyRating component
const DifficultyRating = ({ value, onChange }) => {
    const options = Array.from({ length: 10 }, (_, i) => i + 1);

    const handleToggle = (selectedValue) => {
        if (value === selectedValue) return;
        onChange(selectedValue);
    };

    return (
        <div className="space-y-4 mb-8">
            <h3 className="font-normal mb-4">How hard did this feel on a scale of 1-10?</h3>
            <p className="text-xs font-normal mb-4">(1 being very easy, 10 being extremely challenging)</p>
            <div className="mb-4">
                <div className="flex flex-wrap gap-2 mt-1">
                    {options.map((option) => (
                        <Button
                            key={option}
                            type="button"
                            variant={value === option ? "default" : "outline"}
                            onClick={() => handleToggle(option)}
                            className={cn(
                                "text-xs py-2 px-4 rounded-full shadow-none transition-colors border-2 hover:bg-[#0F213F]/5",
                                value === option
                                    ? "bg-[#0F213F] text-white hover:bg-[#0F213F]"
                                    : "text-gray-700 border-gray-200 border-2 hover:bg-[#0F213F]/5",
                            )}
                        >
                            {option}
                        </Button>
                    ))}
                </div>
            </div>
        </div>
    )
}

// Main FeedbackDialog component
const FeedbackDialog = ({ isOpen, onClose, workout }) => {
    const [completionStatus, setCompletionStatus] = useState('')
    const [difficultyRating, setDifficultyRating] = useState(null)
    const [notes, setNotes] = useState('')
    const [loading, setLoading] = useState(false)

    const { getToken } = useAuth()
    const router = useRouter()
    const params = useParams()

    const triggerConfetti = useConfetti(false)

    // track dialog open event
    const { trackEvent } = useMixpanel()
    useEffect(() => {
        if (isOpen) {
            const { planId, workoutId } = params
            trackEvent('Workout Tracking Started', {
                plan_id: planId,
                workout_id: workoutId,
                date: workout?.date,
                workout_type: workout?.workout_info?.type
            })
        }
    }, [isOpen])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        const token = getToken()
        const { planId, workoutId } = params
        const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/plans/${planId}/workouts/${workoutId}/`
        const payload = {
            completion_status: completionStatus,
            difficulty: difficultyRating,
            additional_notes: notes
        }
        try {
            const response = await fetch(url, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Token ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            if (response.ok) {
                const data = await response.json()
                toast(
                    <div className='flex flex-col items-center justify-center gap-4 p-6'>
                        <Check className="w-10 h-10" />
                        <span className="font-cormorant text-2xl text-center">Got it! I&apos;ll incorporate this into your future training!</span>
                    </div>
                )
                triggerConfetti()
                router.push(`/plans/${planId}`)
            } else {
                if (response.status === 400) {
                    toast.error('Bad Request: Please check your input.')
                } else if (response.status === 401) {
                    toast.error('Unauthorized: Please log in again.')
                } else if (response.status === 403) {
                    toast.error('Forbidden: You are not allowed to perform this action.')
                } else if (response.status === 404) {
                    toast.error('Not Found: The workout could not be found.')
                } else {
                    toast.error('An error occurred. Please try again.')
                }
            }
        } catch (error) {
            toast.error('Network error: Please try again later.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent
                className="sm:max-w-[50vh] max-h-[calc(100dvh)] p-0 overflow-hidden flex flex-col gap-0"
                onOpenAutoFocus={(e) => e.preventDefault()}
            >
                {/* Sticky Header */}
                <DialogHeader className="sticky top-0 z-5 bg-white p-4 border-b border-[#C0D9C5]/50">
                    <DialogTitle className="font-cormorant font-normal text-2xl text-left">
                        {workout?.workout_info?.title ? workout.workout_info.title : workout?.workout_info?.type}
                    </DialogTitle>
                </DialogHeader>

                {/* Scrollable content */}
                <div className="flex-1 overflow-y-auto p-4">
                    <CompletionStatus
                        value={completionStatus}
                        onChange={setCompletionStatus}
                    />

                    <DifficultyRating
                        value={difficultyRating}
                        onChange={setDifficultyRating}
                    />

                    <div className="space-y-2 mb-4">
                        <h3 className="font-normal mb-4">Help me make your plan better</h3>
                        <Textarea
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            className="w-full h-36 p-4 rounded-md border-2 border-gray-200 focus:border-[#0F213F] focus:ring-0 whitespace-pre-line min-h-[170px] placeholder:text-sm"
                            placeholder={`- If you just ran, what were your average pace and interval paces?
                            - Overall, how is your body feeling?
                            - Any questions?
                            Every detail helps me better meet you where you are.`}
                        />

                    </div>
                </div>

                {/* Sticky Footer */}
                {!!completionStatus && (
                    <div className="sticky bottom-0 z-10 bg-white border-t border-gray-200 p-2">
                        <Button
                            className="w-full px-8 py-4 h-12"
                            variant="ghost"
                            onClick={handleSubmit}
                            disabled={loading || !completionStatus}
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                'Save Progress'
                            )}
                        </Button>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    )
}

export default FeedbackDialog