"use client"

import { useEffect, useState, useMemo } from 'react'
import { useAuth } from '@/context/AuthProvider'
import withAuth from '@/hoc/withAuth'
import { useParams, useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Card, CardContent } from "@/components/ui/card"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
    ChevronLeft,
    Clock,
    Activity,
    Dumbbell,
    CheckCircle,
    UserRoundPen,
    XCircle,
    Utensils,
} from 'lucide-react'
import { cn, getWorkoutColor } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import FeedbackDialog from '@/components/workout/FeedbackDialog'
import { useMixpanel } from "@/context/MixpanelProvider"
import { useNotFound } from '@/context/With404Boundary'


const WorkoutHeader = () => (
    <header className="w-screen border-b sticky top-0 z-10 min-h-[64px] bg-white">
        <div className="max-w-4xl mx-auto px-4 flex items-center min-h-[64px]">
            <Button
                onClick={() => window.history.back()}
                variant="ghost"
                size="icon"
            >
                <ChevronLeft />
            </Button>
            <span
                onClick={() => window.history.back()}
                className="cursor-pointer"
            >
                Back to Calendar
            </span>
        </div>
    </header>
)

const WorkoutDot = ({ type, large = false }) => {
    const color = useMemo(() => getWorkoutColor(type), [type]);
    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger>
                    <Avatar
                        className={cn(
                            large && "h-3 w-3",
                            !large && "h-1.5 w-1.5",
                        )}
                        style={{ backgroundColor: color }}
                    />
                </TooltipTrigger>
                <TooltipContent>{type}</TooltipContent>
            </Tooltip>
        </TooltipProvider>
    )
}

const WorkoutTitle = ({ workout }) => {

    const workoutIcon = useMemo(() => {
        switch (workout?.completion_status) {
            case "completed":
                return <CheckCircle className="w-5 h-5" />
            case "skipped":
                return <XCircle className="w-5 h-5" />
            case "modified":
                return <UserRoundPen className="w-5 h-5" />
            default:
                return null
        }
    }, [workout])

    if (!workout) {
        return null
    }

    return (
        <div className="pb-2 mb-6">
            <div className="flex items-center">
                <WorkoutDot type={workout?.workout_info?.type} large={true} />
                <span className="ml-2 text-xs uppercase">{workout?.workout_info?.type}</span>
            </div>
            <div className="font-bold flex items-center gap-2 mt-2">
                <span className="font-cormorant text-2xl italic">
                    {workout?.workout_info?.title ? workout.workout_info.title : workout?.workout_info?.type}
                </span>
                {workoutIcon && (
                    <span className="ml-2">{workoutIcon}</span>
                )}
            </div>
        </div>
    )
}

const MetricCard = ({ icon, title, value }) => {
    if (!value) {
        return null
    }
    return (
        <Card className="transition-all shadow-none hover:shadow-md border border-black">
            <CardContent className="p-3">
                <div className="flex items-center gap-2 mb-2">
                    <div className="flex items-center justify-center">{icon}</div>
                    <h3 className="text-xs text-athletic-charcoal/60">{title}</h3>
                </div>
                <p className="font-semibold">{value}</p>
            </CardContent>
        </Card>
    )
};

const WorkoutStructure = ({ steps }) => {
    if (!steps || steps.length === 0) {
        return null
    }
    return (
        <div className="space-y-6 mb-8">
            {steps.map((step, index) => (
                <div key={index} className="flex gap-4">
                    {/* Left column: number + line */}
                    <div className="flex flex-col items-center">
                        {/* Circle with number */}
                        <div className="w-6 h-6 rounded-full bg-athletic-mint flex items-center justify-center">
                            <span className="font-semibold text-athletic-navy text-sm">
                                {index + 1}
                            </span>
                        </div>
                        {/* Vertical line */}
                        <div className="w-[1px] flex-1 bg-gray-300 mt-1" />
                    </div>

                    {/* Right column: content */}
                    <div className="flex-1 bg-white rounded-md p-4 border border-[#0A1E32]">
                        <h3 className="text-sm font-semibold mb-2">{step.name}</h3>
                        <p className="whitespace-pre-line">{step.description}</p>
                    </div>
                </div>
            ))}
        </div>
    )
}

const TrainerNotes = ({ notes, trainerName }) => (
    <div className="bg-gradient-to-r from-gray-50 to-white rounded-md p-6 mb-8 shadow-none">
        <div className="flex items-center gap-4 mb-4">
            <Avatar>
                <AvatarImage src="/emmi.jpg" alt="Trainer Avatar" style={{ border: 0, objectFit: 'cover' }} />
                <AvatarFallback>EM</AvatarFallback>
            </Avatar>
            <div>
                <h3 className="text-sm font-semibold">Trainer Notes</h3>
                <p className="text-sm text-athletic-charcoal/60">From {trainerName}</p>
            </div>
        </div>
        <p className="">{notes}</p>
    </div>
)

const FuelingTips = ({ beforeTips, afterTips}) => {
    if (!beforeTips && !afterTips) {
        return null
    }
    return (
        <div className="mb-24">
            <h3 className="flex items-center justify-start gap-2 font-semibold mb-4 text-athletic-navy">Fueling Tips <Utensils className="w-4 h-4 text-athletic-navy" /></h3>
            {!!beforeTips && (
                <div className="flex-1 bg-white rounded-md p-4 border border-gray-200 mb-6">
                    <h3 className="text-sm font-semibold mb-2">Before Workout</h3>
                    {beforeTips.map((tip, index) => (
                        <p key={index} className="mb-2">
                            {tip}
                        </p>
                    ))}
                </div>
            )}
            {!!afterTips && (
                <div className="flex-1 bg-white rounded-md p-4 border border-gray-200 mb-6">
                    <h3 className="text-sm font-semibold mb-2">After Workout</h3>
                    {afterTips.map((tip, index) => (
                        <p key={index} className="mb-2">
                            {tip}
                        </p>
                    ))}
                </div>
            )}
        </div>
    )
}

const CompletionButton = ({ onClick }) => (
    <div className="fixed inset-x-0 bottom-0 bg-white border-t border-athletic-mint p-4 shadow-md">
        <div className="max-w-4xl mx-auto">
            <Button
                className="w-full text-white h-12 bg-[#0F213F]"
                onClick={onClick}
            >
                HOW&apos;D IT GO?
            </Button>
        </div>
    </div>
)

function WorkoutPage() {
    const params = useParams();
    const planId = params.planId;
    const workoutId = params.workoutId;
    const router = useRouter()
    const { getToken } = useAuth()

    const [workout, setWorkout] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    const [isFeedbackDialogOpen, setIsFeedbackDialogOpen] = useState(false)

    const { markNotFound } = useNotFound()
    
    useEffect(() => {
        if (!planId || !workoutId) {
            setError('Missing workout or plan identifier.')
            setLoading(false)
            return
        }
        const token = getToken()
        if (!token) {
            setError('Authentication token not found.')
            setLoading(false)
            return
        }
        const fetchWorkout = async () => {
            try {
                const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/plans/${planId}/workouts/${workoutId}/`, {
                    headers: {
                        'Authorization': `Token ${token}`
                    }
                }
                )
                if (response.status === 403 || response.status === 404) {
                    markNotFound()
                    return
                }
                if (!response.ok) {
                    setError('An error occurred while fetching workout details.')
                    setLoading(false)
                    return
                }
                const data = await response.json()
                setWorkout(data)
            } catch (err) {
                setError('An unexpected error occurred.')
            } finally {
                setLoading(false)
            }
        }
        fetchWorkout()
    }, [planId, workoutId, getToken, router])

    const { user } = useAuth()
    const { trackEvent } = useMixpanel()
    useEffect(() => {
        if (workout && user && user.id) {
            trackEvent('Workout Viewed', {
                plan_id: planId,
                workout_id: workoutId,
                date: workout?.date,
                workout_type: workout?.workout_info?.type
            })
        }
    }, [user, workout])

    return (
        <ScrollArea className="h-dvh">
            <WorkoutHeader />
            <main className="max-w-4xl mx-auto px-4 py-6">
                {loading ? (
                    <div className="max-w-4xl mx-auto px-4 py-6">
                        <Skeleton className="h-8 w-full mb-4" />
                        <Skeleton className="h-6 w-3/4 mb-4" />
                        <Skeleton className="h-4 w-full" />
                    </div>
                ) : (
                    error ? (
                        <div className="max-w-4xl mx-auto px-4 py-6">
                            <p className="text-red-500">{error}</p>
                        </div>
                    ) : (
                        <>
                            <WorkoutTitle workout={workout} />
                            <div className="grid grid-cols-3 gap-4 mb-8">
                                <MetricCard
                                    icon={<Clock className="w-5 h-5 text-athletic-navy" />}
                                    title="Duration"
                                    value={workout?.workout_info?.duration ? `${workout?.workout_info?.duration} minutes` : null}
                                />
                                <MetricCard
                                    icon={<Activity className="w-5 h-5 text-athletic-navy" />}
                                    title="Distance"
                                    value={workout?.workout_info?.distance ? `${workout?.workout_info?.distance} miles` : null}
                                />
                                <MetricCard
                                    icon={<Dumbbell className="w-5 h-5 text-athletic-navy" />}
                                    title="Effort"
                                    value={workout?.workout_info?.effort ? workout?.workout_info?.effort : null}
                                />
                            </div>
                            <TrainerNotes notes={workout?.workout_info?.notes} trainerName="Emmi" />
                            <WorkoutStructure steps={workout?.workout_info?.steps} />
                            <FuelingTips beforeTips={workout?.workout_info?.before_tips} afterTips={workout?.workout_info?.after_tips}/>
                        </>
                    )
                )}
            </main>
            {workout?.completion_status === "not_completed" && (
                <>
                    <CompletionButton onClick={() => setIsFeedbackDialogOpen(true)} />
                    <FeedbackDialog
                        isOpen={isFeedbackDialogOpen}
                        onClose={(updateWorkout) => {
                            if (!!updateWorkout) fetchWorkout()
                                setIsFeedbackDialogOpen(false)
                        }}
                        workout={workout}
                    />
                </>
            )}
        </ScrollArea>
    )
}

export default withAuth(WorkoutPage)