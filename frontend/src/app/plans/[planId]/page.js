"use client"

import withAuth from '@/hoc/withAuth'
import { useAuth } from "@/context/AuthProvider"
import { useState, useEffect, useMemo, Suspense } from 'react'
import {
    format,
    addDays,
    differenceInCalendarWeeks,
    startOfWeek,
    isSameDay,
    isToday,
    parseISO,
    startOfDay
} from 'date-fns'
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar } from "@/components/ui/avatar"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Skeleton } from "@/components/ui/skeleton"
import { useRouter, useParams, useSearchParams } from 'next/navigation'
import {
    ChevronLeft,
    ChevronRight,
    CheckCircle,
    UserRoundPen,
    XCircle,
    LogOut,
    MoveRight
} from 'lucide-react'
import { cn, getWorkoutColor } from '@/lib/utils'
import { useMixpanel } from "@/context/MixpanelProvider";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog"
import { useNotFound } from '@/context/With404Boundary'
import LoadingScreen from '@/components/ui/loading-screen';


// WorkoutDot component
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

// WeekView component
const WeekView = ({ currentDate, onDateSelect, workouts }) => {
    const weekStart = useMemo(() => startOfWeek(currentDate, { weekStartsOn: 1 }), [currentDate])
    const days = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart])

    const workoutsByDate = useMemo(() => {
        return workouts.reduce((acc, workout) => {
            const date = startOfDay(parseISO(workout.date))
            const formattedDate = format(date, 'yyyy-MM-dd')
            acc[formattedDate] = acc[formattedDate] || []
            acc[formattedDate].push(workout)
            return acc
        }, {})
    }, [workouts])

    return (
        <ScrollArea className="w-full whitespace-nowrap">
            <div className="flex justify-center">
                <div className="flex space-x-4 pb-4">
                    {days.map((day) => (
                        <div
                            key={day.toISOString()}
                            className={cn(
                                "flex flex-col items-center p-2 rounded-md cursor-pointer gap-1.5",
                                isSameDay(day, currentDate) && "bg-blue-950",
                                isToday(day) && "border-2 border-blue-950"
                            )}
                            onClick={() => onDateSelect(day)}
                        >
                            <span className="text-xs text-gray-500 uppercase">{format(day, 'EEE')}</span>
                            <span
                                className={cn(
                                    "font-semibold",
                                    isSameDay(day, currentDate) && "text-white"
                                )}
                            >{format(day, 'd')}</span>
                            <div className="flex space-x-1 mt-1">
                                {workoutsByDate[format(day, 'yyyy-MM-dd')]?.map((workout, index) => (
                                    <WorkoutDot key={index} type={workout?.workout_info?.type} />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <ScrollBar orientation="horizontal" />
        </ScrollArea>
    )
}

// WorkoutCard component
const WorkoutCard = ({ workout }) => {
    const router = useRouter()

    const handleClick = () => {
        router.push(`/plans/${workout.plan}/workouts/${workout.id}`)
    }

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

    return (
        <Card className="mb-4 rounded-md border-black cursor-pointer shadow-none hover:shadow-lg transition-shadow" onClick={handleClick}>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between w-full">
                    <div className="flex items-center">
                        <WorkoutDot type={workout?.workout_info?.type} large={true} />
                        <span className="ml-2 text-xs uppercase">{workout?.workout_info?.type}</span>
                    </div>
                    {workoutIcon && (
                        <span className="ml-2">{workoutIcon}</span>
                    )}
                </div>
                <CardTitle className="flex items-center ">
                    <span className="font-cormorant font-bold text-2xl italic">
                        {workout?.workout_info?.title ? workout.workout_info.title : workout?.workout_info?.type}
                    </span>
                    <MoveRight className="ml-3 w-5 h-5" strokeWidth={1}/>
                </CardTitle>
            </CardHeader>
            <CardContent>
                {workout?.workout_info?.duration && (
                    <p className="text-sm mb-2">{workout?.workout_info?.duration} minutes</p>
                )}
                <p className="text-xs">{workout?.workout_info?.summary}</p>
            </CardContent>
        </Card>
    )
}

// Main TrainingPlan component
const TrainingPlan = () => {

    const router = useRouter()
    const searchParams = useSearchParams();
    const queryDate = searchParams.get('date');

    const [currentDate, setCurrentDate] = useState(() => {
        return queryDate ? parseISO(queryDate) : new Date();
    });

    const updateUrlWithDate = (date) => {
        const formattedDate = format(date, 'yyyy-MM-dd');
        const currentParams = new URLSearchParams(window.location.search);
        currentParams.set('date', formattedDate);
        router.push(`?${currentParams.toString()}`, undefined, { shallow: true });
    };

    const handleDateChange = (date) => {
        setCurrentDate(date);
        updateUrlWithDate(date);
    };

    const [currentWeek, setCurrentWeek] = useState(() => {
        const start = startOfWeek(currentDate, { weekStartsOn: 1 });
        const end = addDays(start, 6);
        return [start, end];
    });
    const [workouts, setWorkouts] = useState([])
    const [loading, setLoading] = useState(true)
    const [planDetails, setPlanDetails] = useState(null)
    const [planError, setPlanError] = useState('')
    const [workoutError, setWorkoutError] = useState('')
    const { user, logout } = useAuth()

    const params = useParams();
    const planId = params.planId;

    useEffect(() => {
        const newStart = startOfWeek(currentDate, { weekStartsOn: 1 })
        const newEnd = addDays(newStart, 6)

        const [prevStart, prevEnd] = currentWeek

        if (!isSameDay(prevStart, newStart) || !isSameDay(prevEnd, newEnd)) {
            setCurrentWeek([newStart, newEnd])
        }
    }, [currentDate])

    const formattedWeekRange = useMemo(() => {
        const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 }); // Monday
        const weekEnd = addDays(weekStart, 6);

        const startMonth = format(weekStart, 'MMMM').toUpperCase();
        const endMonth = format(weekEnd, 'MMMM').toUpperCase();
        const startDay = format(weekStart, 'd');
        const endDay = format(weekEnd, 'd');

        // Check if the endMonth is different from the startMonth
        if (startMonth !== endMonth) {
            return `${startMonth} ${startDay}–${endMonth} ${endDay}`;
        }

        return `${startMonth} ${startDay}–${endDay}`;
    }, [currentDate]);

    const activeWeekIndex = useMemo(() => {
        if (!planDetails?.plan_info?.weeks || !currentDate) return undefined;
    
        const weeks = planDetails.plan_info.weeks;
    
        // Check if all weeks have week_start_date
        const hasNewWeekDates = weeks.every(week => week.week_start_date);
    
        if (hasNewWeekDates) {
            const currentMonday = startOfWeek(currentDate, { weekStartsOn: 1 });
    
            const index = weeks.findIndex(week => {
                const weekStart = startOfWeek(parseISO(week.week_start_date), { weekStartsOn: 1 });
                return weekStart.getTime() === currentMonday.getTime();
            });
    
            return index >= 0 ? index : undefined;
        }
    
        // Legacy logic – TODO: remove this once legacy data is fixed
        const planCreatedAt = planDetails.created_at;
        if (!planCreatedAt) return undefined;
    
        const startOfPlanWeek = startOfWeek(new Date(planCreatedAt), { weekStartsOn: 1 });
        const startOfGivenWeek = startOfWeek(currentDate, { weekStartsOn: 1 });
        const index = differenceInCalendarWeeks(startOfGivenWeek, startOfPlanWeek, { weekStartsOn: 1 });
    
        return index >= 0 && index < weeks.length ? index : undefined;
    }, [planDetails, currentDate]);

    const { markNotFound } = useNotFound()

    useEffect(() => {
        if (!planId) return;
        setLoading(true);
        setWorkoutError('');
        // Format dates as YYYY-MM-DD
        const formattedWeekStart = currentWeek[0].toISOString().split('T')[0];
        const formattedWeekEnd = currentWeek[1].toISOString().split('T')[0];
        fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/plans/${planId}/workouts/?start_date=${formattedWeekStart}&end_date=${formattedWeekEnd}`, {
            headers: {
                Authorization: `Token ${user.token}`
            }
        })
            .then(response => {
                if (response.status === 403 || response.status === 404) {
                    markNotFound()
                    return
                }
                if (!response.ok) {
                    throw new Error('Failed to fetch workouts');
                }
                return response.json();
            })
            .then(data => {
                // Assuming the API returns an array in a "results" field if paginated
                setWorkouts(data.results || data);
                setLoading(false);
            })
            .catch(error => {
                setWorkoutError(error.message);
                setLoading(false);
            });
    }, [planId, currentWeek]);

    useEffect(() => {
        if (!planId) return;
        fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/plans/${planId}/`, {
            headers: {
                Authorization: `Token ${user.token}`
            }
        })
            .then(response => {
                if (response.status === 403 || response.status === 404) {
                    markNotFound()
                    return
                }
                if (!response.ok) {
                    throw new Error('Failed to fetch plan details');
                }
                return response.json();
            })
            .then(data => {
                setPlanDetails(data);
            })
            .catch(error => {
                setPlanError(error.message);
            });
    }, [planId]);

    const { trackEvent } = useMixpanel();
    useEffect(() => {
        if (planId && user && user.id) {
            trackEvent('Training Plan Viewed', { plan_id: planId })
        }
    }, [planId])

    const handlePrevWeek = () => {
        const startOfCurrentWeek = startOfWeek(currentDate, { weekStartsOn: 1 });
        const previousMonday = addDays(startOfCurrentWeek, -7);

        // Check if the user is going back to the current week
        const today = new Date();
        const startOfThisWeek = startOfWeek(today, { weekStartsOn: 1 });

        if (isSameDay(previousMonday, startOfThisWeek)) {
            handleDateChange(today);
        } else {
            handleDateChange(previousMonday);
        }
    };

    const handleNextWeek = () => {
        const startOfNextWeek = addDays(startOfWeek(currentDate, { weekStartsOn: 1 }), 7);
        handleDateChange(startOfNextWeek);
    };

    const workoutsOfCurrentDay = workouts.filter(workout =>
        isSameDay(startOfDay(parseISO(workout.date)), startOfDay(currentDate))
    )

    if (!planDetails) {
        return <LoadingScreen />;
    }

    return (
        <div>
            {planError && <p className="text-red-500">{planError}</p>}
            <div className="w-screen border-b">
                <div className="max-w-4xl mx-auto px-4 flex justify-between items-center">
                    <h1 className="text-2xl font-cormorant py-4">{`${user.first_name.split(' ')[0]}'s Training Plan`}</h1>
                    <div>
                        <Dialog>
                            <DialogTrigger>
                                <LogOut className="w-5 h-5 cursor-pointer" strokeWidth={1} />
                            </DialogTrigger>
                            <DialogContent className="p-0">
                                <DialogHeader className="p-4 border-b border-[#C0D9C5]/50">
                                    <DialogTitle className="font-cormorant font-normal text-2xl text-left">
                                        Running away?
                                    </DialogTitle>
                                </DialogHeader>
                                <DialogDescription className="p-4">
                                    Whenever you&apos;re ready, you can log back in, and your plan will still be here.<br /><br />
                                    Feel free to text me if you have any questions.
                                </DialogDescription>
                                <DialogFooter className="px-4 pb-4 flex flex-row justify-end">
                                    <Button
                                        variant="destructive"
                                        className="mr-2 w-20 bg-[#800020] text-white"
                                        onClick={() => logout()}
                                    >
                                        LOG OUT
                                    </Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </div>
                </div>
            </div>
            <div className="max-w-4xl mx-auto p-4">
                <div className="flex justify-between items-center mb-6 mt-4">
                    <Button
                        onClick={handlePrevWeek}
                        variant="outline"
                        size="icon"
                        className="rounded-full"
                    >
                        <ChevronLeft />
                    </Button>
                    <span className="uppercase text-xs">
                        {formattedWeekRange}
                    </span>
                    <Button
                        onClick={handleNextWeek}
                        variant="outline"
                        size="icon"
                        className="rounded-full"
                    >
                        <ChevronRight />
                    </Button>
                </div>
                {workoutError && <p className="text-red-500 mb-4">{workoutError}</p>}
                <WeekView currentDate={currentDate} onDateSelect={handleDateChange} workouts={workouts} />
                {activeWeekIndex !== undefined && (
                    <div className="p-4 border rounded-md mb-8">
                        <h3 className="text-sm font-semibold mb-2">Week {activeWeekIndex} Focus</h3>
                        <span className="text-xs">{planDetails?.plan_info?.weeks[activeWeekIndex]?.goal}</span>
                    </div>
                )}

                {loading ? (
                    <div className="space-y-4">
                        <Skeleton className="h-24 w-full" />
                        <Skeleton className="h-24 w-full" />
                        <Skeleton className="h-24 w-full" />
                    </div>
                ) : workoutsOfCurrentDay.length > 0 ? (
                    workoutsOfCurrentDay.map((workout, index) => (
                        <WorkoutCard key={index} workout={workout} />
                    ))
                ) : (
                    <div className="flex items-center justify-center h-40">
                        <p className="text-sm text-gray-500">No workouts scheduled for this day.</p>
                    </div>
                )}
            </div>
        </div>
    )
}

const TrainingPlanPage = () => {
    return (
        <Suspense fallback={<LoadingScreen />}>
            <TrainingPlan />
        </Suspense>
    );
}


export default withAuth(TrainingPlanPage)