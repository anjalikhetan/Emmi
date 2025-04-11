"use client"

import withAuth from '@/hoc/withAuth'
import { useAuth } from "@/context/AuthProvider"
import { useState, useEffect } from 'react'
import { useForm, FormProvider, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DatePicker } from '@/components/date-picker'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useSearchParams, useRouter } from 'next/navigation'
import { toast } from "sonner"
import { useMixpanel } from "@/context/MixpanelProvider";
import { ArrowLeft } from 'lucide-react'
import { format } from "date-fns";


// Define the schema for form validation
const formSchema = z
  .object({
    name: z
      .string()
      .trim()
      .min(2, "Name must be at least 2 characters"),
    age: z.preprocess(
      (val) => {
        const num = Number(val);
        return isNaN(num) ? undefined : num;
      },
      z.number({
        invalid_type_error: "Please enter a valid age",
        required_error: "Age is required",
      })
        .min(18, "You must be at least 18 years old")
        .max(120, "Please enter a realistic age")
    ),
    feet: z.preprocess(
      (val) => (val === "" || isNaN(val) ? undefined : Number(val)),
      z.number({
        invalid_type_error: "Feet must be a whole number",
      })
        .int("Feet must be a whole number")
        .min(1, "Feet must be between 1 and 8")
        .max(8, "Feet must be between 1 and 8")
        .optional()
    ),
    inches: z.preprocess(
      (val) => (val === "" || isNaN(val) ? undefined : Number(val)),
      z.number({
        invalid_type_error: "Inches must be a whole number",
      })
        .int("Inches must be a whole number")
        .min(0, "Inches must be between 0 and 11")
        .max(11, "Inches must be between 0 and 11")
        .optional()
    ),
    heightCm: z.preprocess(
      (val) => (val === "" || isNaN(val) ? undefined : Number(val)),
      z.number().min(100, "Height in cm must be between 100 and 250").max(250, "Height in cm must be between 100 and 250").optional()
    ),
    weightKg: z.preprocess(
      (val) => (val === "" || isNaN(val) ? undefined : Number(val)),
      z.number().min(10, "Weight in kg must be between 10 and 500").max(500, "Weight in kg must be between 10 and 500").optional()
    ),
    weightLbs: z.preprocess(
      (val) => (val === "" || isNaN(val) ? undefined : Number(val)),
      z.number().min(22, "Weight in lbs must be between 22 and 1100").max(1100, "Weight in lbs must be between 22 and 1100").optional()
    ),
    goals: z.array(z.string()).min(1, "Please select at least one goal"),
    goalsDetails: z.string().optional(),
    raceName: z.string().optional(),
    raceDate: z
      .string()
      .optional()
      .refine(val => !val || /^\d{4}-\d{2}-\d{2}$/.test(val), {
        message: "Date must be in format YYYY-MM-DD"
    }),
    distance: z.string().optional(),
    timeGoal: z.string().optional(),
    runningExperience: z.string().optional(),
    routineDaysPerWeek: z.string().optional(),
    routineMilesPerWeek: z.string().optional(),
    routineEasyPace: z.string().optional(),
    routineLongestRun: z.string().optional(),
    recentRaceResults: z.string().optional(),
    extraTraining: z.array(z.string()).default([]),
    diet: z.array(z.string()).default([]),
    injuries: z.string().optional(),
    daysCommitTraining: z.string().optional(),
    preferredLongRunDays: z.array(z.string()).default([]),
    preferredWorkoutDays: z.array(z.string()).default([]),
    preferredRestDays: z.array(z.string()).default([]),
    otherObligations: z.string().optional(),
    pastProblems: z.array(z.string()).default([]),
    moreInfo: z.string().optional(),
  })
  .refine((data) => {
    const hasFeetInches = data.feet !== undefined || data.inches !== undefined;
    const hasCm = data.heightCm !== undefined;
    return !(hasFeetInches && hasCm);
  }, { message: "Please provide height in either cm or ft/in, but not both", path: ["height"] })
  .refine((data) => {
    const hasKg = data.weightKg !== undefined;
    const hasLbs = data.weightLbs !== undefined;
    return !(hasKg && hasLbs);
  }, { message: "Please provide weight in either kg or lbs, but not both", path: ["weight"] });


const Header = ({ title, subTitle}) => {
  return (
    <div className="flex flex-col items-center my-6">
      <h1 className="font-cormorant text-3xl text-athletic-navy text-center mb-3">
        {title}
      </h1>
      <span className="uppercase text-xs">{subTitle}</span>
    </div>
  )
}

// ProgressBar component
const ProgressBar = ({ currentStep, totalSteps }) => {
  const progress = (currentStep / totalSteps) * 100
  return <Progress value={progress} className="mb-4 bg-[#C0D9C5]" />
}

// InputField component
const InputField = ({ label, register, name, type = "text", error, placeholder }) => {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <Input 
        className="mt-1"
        type={type}
        placeholder={placeholder}
        {...register(name, { valueAsNumber: type === "number" })}
      />
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
};

// SelectField component
const SelectField = ({ label, options, name, setValue, watch, error }) => {
  const selectedValue = watch(name, "");

  const handleChange = (value) => {
    const selected = options.find((opt) => opt.value === value);
    setValue(name, selected?.label || ""); // ✅ Store label instead of value
  };

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <Select onValueChange={handleChange}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select an option">
            {selectedValue || "Select an option"}
          </SelectValue>
        </SelectTrigger>
        <SelectContent className="max-w-[90vw]">
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
};

// ToggleButtonGroup component
const ToggleButtonGroup = ({
  label,
  options,
  name,
  setValue,
  watch,
  error,
  forceSingleLine = false,
}) => {
  const selectedLabels = watch(name, []);

  const handleToggle = (value) => {
    const selected = options.find((opt) => opt.value === value);
    if (!selected) return;

    const newSelected = selectedLabels.includes(selected.label)
      ? selectedLabels.filter((item) => item !== selected.label)
      : [...selectedLabels, selected.label];

    setValue(name, newSelected);
  };

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-3">{label}</label>
      <div
        className={cn(
          "mt-1 gap-2",
          forceSingleLine ? "flex flex-nowrap overflow-hidden" : "flex flex-wrap"
        )}
      >
        {options.map((option) => (
          <Button
            key={option.value}
            type="button"
            variant={selectedLabels.includes(option.label) ? "default" : "outline"}
            onClick={() => handleToggle(option.value)}
            className={cn(
              "text-xs py-2 px-3 rounded-full shadow-none",
              {
                "text-gray-700 border-gray-200 border-2": !selectedLabels.includes(option.label),
                "bg-[#0F213F] hover:bg-[#0F213F] text-white": selectedLabels.includes(option.label),
                "flex-1 min-w-0 truncate": forceSingleLine, // Only apply squeeze styles when needed
              }
            )}
            style={forceSingleLine ? { flexShrink: 1 } : {}}
          >
            {option.label}
          </Button>
        ))}
      </div>
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
};

// DatePickerField component
const DatePickerField = ({ label, control, name, error }) => {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <Controller
        name={name}
        control={control}
        render={({ field: { onChange, value } }) => (
          <DatePicker
            value={value ? new Date(value) : null} // Convert string back to Date
            onChange={(date) => {
              if (date) {
                const formatted = format(date, "yyyy-MM-dd");
                onChange(formatted);
              } else {
                onChange(""); // clear if user clears date
              }
            }}
            className="mt-1"
          />
        )}
      />
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
};

// TextareaField component
const TextareaField = ({ label, register, name, error, placeholder, className }) => {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <Textarea
        className={cn(
          "mt-1",
          !!className && className
        )}
        placeholder={placeholder}
        {...register(name)}
      />
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  )
}

const HeightInputField = ({ register, setValue, watch, error }) => {
  const [heightUnit, setHeightUnit] = useState("ft/in");
  const feet = watch("feet", ""); // Track feet input
  const inches = watch("inches", ""); // Track inches input
  const heightCm = watch("heightCm", ""); // Track cm input

  const handleUnitChange = (unit) => {
    setHeightUnit(unit);
    if (unit === "cm") {
      setValue("feet", ""); // Clear feet and inches when switching
      setValue("inches", "");
    } else {
      setValue("heightCm", ""); // Clear cm value when switching
    }
  };

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">Height</label>
      <div className="flex gap-2">
        {heightUnit === "ft/in" ? (
          <>
            <Input
              type="number"
              placeholder="Feet"
              {...register("feet", { valueAsNumber: true })}
              className="w-1/3"
            />
            <Input
              type="number"
              placeholder="Inches"
              {...register("inches", { valueAsNumber: true })}
              className="w-1/3"
            />
          </>
        ) : (
          <Input
            type="number"
            placeholder="Centimeters"
            {...register("heightCm", { valueAsNumber: true })}
            className="w-2/3"
          />
        )}
        <Select onValueChange={handleUnitChange}>
          <SelectTrigger className="w-1/3">
            <SelectValue placeholder={heightUnit} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ft/in">ft/in</SelectItem>
            <SelectItem value="cm">cm</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
};

const WeightInputField = ({ register, setValue, watch, error }) => {
  const [weightUnit, setWeightUnit] = useState("lbs");
  const weightKg = watch("weightKg", ""); // Track kg input
  const weightLbs = watch("weightLbs", ""); // Track lbs input

  const handleUnitChange = (unit) => {
    setWeightUnit(unit);
    if (unit === "lbs") {
      setValue("weightKg", ""); // Clear kg value when switching to lbs
    } else {
      setValue("weightLbs", ""); // Clear lbs value when switching to kg
    }
  };

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">Weight</label>
      <div className="flex gap-2">
        {weightUnit === "lbs" ? (
          <Input
            type="number"
            step="0.1"
            placeholder="Weight (lbs)"
            {...register("weightLbs", { valueAsNumber: true })}
            className="w-2/3"
          />
        ) : (
          <Input
            type="number"
            step="0.1"
            placeholder="Weight (kg)"
            {...register("weightKg", { valueAsNumber: true })}
            className="w-2/3"
          />
        )}
        <Select onValueChange={handleUnitChange}>
          <SelectTrigger className="w-1/3">
            <SelectValue placeholder={weightUnit} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="kg">kg</SelectItem>
            <SelectItem value="lbs">lbs</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
};

// FormStep component
const FormStep = ({ children, onNext, onPrevious, isFirstStep, isLastStep, isLoading, isSkippable = false }) => {
  return (
    <div>
      <div>{children}</div>
      <div className="flex justify-between">
        <Button
          onClick={onNext}
          disabled={isLoading}
          className={cn(
            "w-full bg-[#0F213F] text-white py-3 rounded-md tracking-wider uppercase text-xs font-semibold hover:bg-[#333333] transition-all duration-300 ease-in-out transform hover:-translate-y-1",
            isLastStep && "h-10"
          )}
        >
          {isLoading ? "Loading..." : (isLastStep ? 'Submit' : isSkippable ? 'Skip' : 'Next')}
        </Button>
      </div>
    </div>
  )
}

// Main OnboardingForm component
const OnboardingForm = () => {
  const router = useRouter()

  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const totalSteps = 8 // Total number of steps in the form

  // Sync step with URL on page load or navigation
  const searchParams = useSearchParams();
  useEffect(() => {
    const stepFromUrl = parseInt(searchParams.get('step'), 10);
    if (stepFromUrl && stepFromUrl >= 1 && stepFromUrl <= totalSteps) {
      setCurrentStep(stepFromUrl);
    }
  }, [searchParams]);

  const methods = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      age: '',
      feet: '',
      inches: '',
      heightCm: '',
      weightKg: '', // Separate fields for kg and lbs
      weightLbs: '',
      weightUnit: 'lbs',
      goals: [],
      goalsDetails: '',
      raceName: '',
      raceDate: '',
      distance: '',
      timeGoal: '',
      runningExperience: '',
      routineDaysPerWeek: '',
      routineMilesPerWeek: '',
      routineEasyPace: '',
      routineLongestRun: '',
      recentRaceResults: '',
      extraTraining: [],
      diet: [],
      injuries: '',
      daysCommitTraining: '',
      preferredLongRunDays: [],
      preferredWorkoutDays: [],
      preferredRestDays: [],
      otherObligations: '',
      pastProblems: [],
      moreInfo: '',
    },
  });
  

  const { register, handleSubmit, control, trigger, formState: { errors }, setError } = methods;
  const { getToken, user } = useAuth()

  const { trackEvent } = useMixpanel();
  useEffect(() => {
    if (!user) {
      return
    }
    trackEvent('Onboarding Started')
  }, [user])

  const onSubmit = async (data) => {
    setIsLoading(true)
    const cleanedData = Object.fromEntries(
      Object.entries(data).filter(([_, value]) => {
        return value !== "" && value !== null && value !== undefined && !Number.isNaN(value)
      })
    )
    cleanedData.is_onboarding_complete = true
    cleanedData.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone // e.g. "America/Lima"
    const payload = {
      first_name: cleanedData.name,
      profile: cleanedData,
    }
    // PATCH update to user profile
    const patchEndpoint = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/users/${user.id}/`
    try {
      const patchResponse = await fetch(patchEndpoint, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Token ${getToken()}`
        },
        body: JSON.stringify(payload)
      })
      const patchData = await patchResponse.json()
      if (!patchResponse.ok) {
        Object.keys(patchData).forEach((field) => {
          setError(`profile.${field}`, { type: "manual", message: patchData[field] })
        })
        setIsLoading(false)
        return
      }
      // POST request to training plan generation endpoint
      const planEndpoint = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/plans/generate/`
      const planResponse = await fetch(planEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Token ${getToken()}`
        }
      })
      const planData = await planResponse.json()
      if (!planResponse.ok) {
        toast(planData.error || "Failed to generate training plan")
        setIsLoading(false)
        return
      }
      router.push("/onboarding-confirmation")
    } catch (error) {
      toast(error.message || "Network error")
      setIsLoading(false)
    }
  }

  const updateStepInUrl = (step) => {
    const params = new URLSearchParams(window.location.search);
    params.set('step', step);
    router.push(`?${params.toString()}`, { scroll: false });
  };

  const nextStep = async () => {
    
    const fieldsToValidate = {
      1: ["name"],
      2: ["age", "feet", "inches", "heightCm", "weightKg", "weightLbs"],
      3: ["goals"],
      4: ["raceName", "raceDate", "distance", "timeGoal"],
      5: ["runningExperience", "routineDaysPerWeek", "routineMilesPerWeek", "routineEasyPace", "routineLongestRun", "recentRaceResults"],
      6: ["extraTraining", "diet", "injuries"],
      7: ["daysCommitTraining", "preferredLongRunDays", "preferredWorkoutDays", "preferredRestDays", "otherObligations", "pastProblems"],
      8: ["moreInfo"],
    };
  
    const stepFields = fieldsToValidate[currentStep] || [];
  
    // Perform validation
    if (stepFields.length > 0) {
      const isValid = await trigger(stepFields);
      console.log('Errors:', errors);
      if (!isValid) {
        console.log('Validation failed! Stopping here.');
        return; // Stop if validation fails
      }
    }
  
    // Track event for completed step
    if (user && user.id) {
      // For simplicity, using currentStep as step_number and a hardcoded mapping for step name
      const stepNames = {
        1: "What's your name?",
        2: "Tell me about you",
        3: "What are your running goals?",
        4: "Are you training for a specific event?",
        5: "Where are you in your running journey?",
        6: "Tell me more about your health and fitness",
        7: "Any other preferences?",
        8: "Anything else you’d like me to know?"
      }
      trackEvent('Onboarding Step Completed', { step_number: currentStep, step_name: stepNames[currentStep] })
    } else {
      console.error('User data missing for step completed event')
    }
  
    console.log('Step', currentStep, totalSteps);
    if (currentStep === totalSteps) {
  
      // Manually gather form values
      const formData = methods.getValues();
  
      // Call onSubmit directly with the collected data
      onSubmit(formData);
    } else {
      const newStep = currentStep + 1;
      setCurrentStep(newStep);
      updateStepInUrl(newStep);
    }
  };

  const previousStep = () => {
    if (currentStep > 1) {
      const newStep = currentStep - 1;
      setCurrentStep(newStep);
      updateStepInUrl(newStep);
    }
  };

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit(onSubmit)} className="max-w-md mx-auto px-4 py-8">
        {currentStep > 1 && (
            <Button
              variant="ghost"
              size="icon"
              className="mb-4"
              onClick={previousStep}
              type="button"
              disabled={currentStep === 1}
              >
                <ArrowLeft />
            </Button>
        )}
        <ProgressBar currentStep={currentStep} totalSteps={totalSteps} />
        
        {currentStep === 1 && (
          <FormStep onNext={nextStep} isFirstStep>
            <Header title="What&apos;s your name?" subTitle="You can call me Emmi" />
            <InputField label="Name" name="name" register={register} error={errors.name?.message} />
          </FormStep>
        )}

        {currentStep === 2 && (
          <FormStep onNext={nextStep} onPrevious={previousStep}>
            <Header title="Tell me about you" subTitle="I&apos;LL MAKE A PLAN JUST FOR YOU" />
            <InputField label="Age" name="age" type="number" register={register} error={errors.age?.message} />
            <HeightInputField 
              register={register} 
              setValue={methods.setValue} 
              watch={methods.watch} 
              error={
                errors.feet?.message || 
                errors.inches?.message || 
                errors.heightCm?.message
              }
            />
            <WeightInputField 
              register={register} 
              setValue={methods.setValue} 
              watch={methods.watch} 
              error={
                errors.weightKg?.message || 
                errors.weightLbs?.message
              }
            />
          </FormStep>
        )}

        {currentStep === 3 && (
          <FormStep onNext={nextStep} onPrevious={previousStep}>
            <Header title="What are your running goals?" subTitle="I WANT TO HELP YOU MEET THEM" />
            
            <ToggleButtonGroup
              label="Pick as many as you want"
              name="goals"
              options={[
                { value: 'firstRace', label: 'Run your first race' },
                { value: 'feelBetter', label: 'Feel better in your body' },
                { value: 'personalRecord', label: 'Achieve a new personal record' },
                { value: 'avoidInjury', label: 'Avoid injury' },
                { value: 'runXMiles', label: `Run "x" miles without stopping` },
                { value: 'runFaster', label: 'Run faster' },
                { value: 'fuelingNutrition', label: 'Learn about fueling and nutrition' },
                { value: 'manageStress', label: 'Manage stress/improve mood' },
                { value: 'getOutside', label: 'Get outside' },
                { value: 'getConsistent', label: 'Get consistent' },
                { value: 'findCommunity', label: 'Find community' },
                { value: 'femaleTraining', label: 'Learn about female-specific training' },
                { value: 'joyInRunning', label: 'Find more joy in running' },
                { value: 'strengthTraining', label: 'Incorporate strength training' },
                { value: 'lifelongRunner', label: 'Be a lifelong runner' }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.goals?.message}
            />

            {/* Multi-line input for additional goal details */}
            <TextareaField
              placeholder="Any other goals? Every detail will help me support you better."
              name="goalsDetails"
              register={register}
              error={errors.goalsDetails?.message}
            />
          </FormStep>
        )}

        {currentStep === 4 && (
          <FormStep
            onNext={nextStep}
            onPrevious={previousStep}
            isSkippable={
              !methods.watch("raceName") &&
              !methods.watch("raceDate") &&
              !methods.watch("distance") &&
              !methods.watch("timeGoal")
            }
          >
            <Header title="Are you training for a specific event?" subTitle="IF SO, I&apos;LL TAKE THAT INTO ACCOUNT" />
            <InputField label="Race Name" name="raceName" register={register} error={errors.raceName?.message} />
            <DatePickerField
              label="Race Date"
              name="raceDate"
              control={control}
              error={errors.raceDate?.message}
            />
            {/* Distance Input with Regex Validation */}
            <InputField
              label="Distance"
              name="distance"
              register={register}
              error={errors.distance?.message}
              placeholder="5K, 10K, 42.195KM, 26.2M"
            />

            {/* Time Goal Input with Regex Validation */}
            <InputField
              label="Time Goal"
              name="timeGoal"
              register={register}
              error={errors.timeGoal?.message}
              placeholder="4:10 or 4:10:00"
            />
          </FormStep>
        )}

        {currentStep === 5 && (
          <FormStep onNext={nextStep} onPrevious={previousStep}>
            <Header title="Where are you in your running journey?" subTitle="REMEMBER, WE ALL BEGIN SOMEWHERE" />
            <SelectField
              label="How would you describe your running experience?"
              name="runningExperience"
              options={[
                { value: 'newToRunning', label: 'New to running' },
                { value: 'returningLongBreak', label: 'Returning from a long break' },
                { value: 'returningInjury', label: 'Returning from injury' },
                { value: 'casualRunning', label: 'Run casually but no structured training' },
                { value: 'consistentTraining', label: 'Run consistently and train for races' },
                { value: 'competitiveTraining', label: 'Train competitively with performance goals' },
                { value: 'eliteRunning', label: 'Compete at an elite level' }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.runningExperience?.message}
            />

            {/* Section Label */}
            <h3 className="mt-4 mb-2">
              <label className="block text-sm font-medium text-gray-700">What&apos;s your current running routine?</label>
            </h3>

            {/* Row 1 */}
            <div className="flex gap-4">
              <div className="w-1/2">
                <InputField 
                  label={<span className="text-xs">Days per week running</span>} 
                  placeholder="3" 
                  name="routineDaysPerWeek" 
                  register={register} 
                  error={errors.routineDaysPerWeek?.message} 
                />
              </div>
              <div className="w-1/2">
                <InputField 
                  label={<span className="text-xs">Miles run per week</span>} 
                  placeholder="15 miles" 
                  name="routineMilesPerWeek" 
                  register={register} 
                  error={errors.routineMilesPerWeek?.message} 
                />
              </div>
            </div>

            {/* Row 2 */}
            <div className="flex gap-4">
              <div className="w-1/2">
                <InputField 
                  label={<span className="text-xs">Easy pace</span>} 
                  placeholder="9:30/mile" 
                  name="routineEasyPace" 
                  register={register} 
                  error={errors.routineEasyPace?.message} 
                />
              </div>
              <div className="w-1/2">
                <InputField 
                  label={<span className="text-xs">Longest run in last month</span>} 
                  placeholder="8 miles" 
                  name="routineLongestRun" 
                  register={register} 
                  error={errors.routineLongestRun?.message} 
                />
              </div>
            </div>

            <InputField 
              label="Any recent race results?" 
              placeholder="Napa Half Marathon in 2:05" 
              name="recentRaceResults" 
              register={register} 
              error={errors.recentRaceResults?.message} 
            />
          </FormStep>
        )}

        {currentStep === 6 && (
          <FormStep onNext={nextStep} onPrevious={previousStep}>
            <Header title="Tell me more about your health and fitness" subTitle="I&apos;LL TAKE THAT INTO ACCOUNT" />
            <ToggleButtonGroup
              label="What else do you like to do?"
              name="extraTraining"
              options={[
                { value: 'strengthTrain', label: 'Strength train' },
                { value: 'cycle', label: 'Cycle' },
                { value: 'swim', label: 'Swim' },
                { value: 'elliptical', label: 'Elliptical' },
                { value: 'erg', label: 'Erg' },
                { value: 'stairStepper', label: 'Stair-stepper' },
                { value: 'hiit', label: 'HIIT' },
                { value: 'pilates', label: 'Pilates' },
                { value: 'barre', label: 'Barre' },
                { value: 'yoga', label: 'Yoga' },
                { value: 'hike', label: 'Hike' },
                { value: 'climb', label: 'Climb' },
                { value: 'tennis', label: 'Tennis' },
                { value: 'dance', label: 'Dance' },
                { value: 'surf', label: 'Surf' },
                { value: 'ski', label: 'Ski' }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.extraTraining?.message}
            />
            <ToggleButtonGroup
              label="Do you follow a special diet?"
              name="diet"
              options={[
                { value: 'vegan', label: 'Vegan' },
                { value: 'vegetarian', label: 'Vegetarian' },
                { value: 'pescatarian', label: 'Pescatarian' },
                { value: 'paleo', label: 'Paleo' },
                { value: 'glutenFree', label: 'Gluten-free' },
                { value: 'dairyFree', label: 'Dairy-free' },
                { value: 'noRedMeat', label: 'No red meat' },
                { value: 'nutFree', label: 'Nut-free' },
                { value: 'peanutFree', label: 'Peanut-free' }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.diet?.message}
            />
            <TextareaField
              label="Any injuries or medical conditions that could impact your training?"
              name="injuries"
              register={register}
              error={errors.goalsDetails?.message}
              placeholder="e.g. shin splints, sensitive back, asthma, PCOS"
            />
          </FormStep>
        )}

        {currentStep === 7 && (
          <FormStep onNext={nextStep} onPrevious={previousStep}>
            <Header title="Any other preferences?" subTitle="I WANT TO MAKE SURE YOU CAN STICK TO THE PLAN" />
            <SelectField
              label="How many days a week can you commit to training?"
              name="daysCommitTraining"
              options={[
                { value: '1day', label: '1 day' },
                { value: '2days', label: '2 days' },
                { value: '3days', label: '3 days' },
                { value: '4days', label: '4 days' },
                { value: '5days', label: '5 days' },
                { value: '6days', label: '6 days' },
                { value: '7days', label: '7 days' }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.daysCommitTraining?.message}
            />
            <h3 className="mt-4 mb-2">
              <label className="block text-sm font-medium text-gray-700">Preferred days for long runs, speed sessions, rest days?</label>
            </h3>
            <ToggleButtonGroup
              label="Long run"
              name="preferredLongRunDays"
              forceSingleLine={true}
              options={[
                { value: 'monday', label: 'M' },
                { value: 'tuesday', label: 'Tu' },
                { value: 'wednesday', label: 'W' },
                { value: 'thursday', label: 'Th' },
                { value: 'friday', label: 'F' },
                { value: 'saturday', label: 'Sa' },
                { value: 'sunday', label: 'Su' }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.preferredLongRunDays?.message}
            />
            <ToggleButtonGroup
              label="Speed sessions"
              name="preferredWorkoutDays"
              forceSingleLine={true}
              options={[
                { value: 'monday', label: 'M' },
                { value: 'tuesday', label: 'Tu' },
                { value: 'wednesday', label: 'W' },
                { value: 'thursday', label: 'Th' },
                { value: 'friday', label: 'F' },
                { value: 'saturday', label: 'Sa' },
                { value: 'sunday', label: 'Su' }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.preferredWorkoutDays?.message}
            />
            <ToggleButtonGroup
              label="Rest days"
              name="preferredRestDays"
              forceSingleLine={true}
              options={[
                { value: 'monday', label: 'M' },
                { value: 'tuesday', label: 'Tu' },
                { value: 'wednesday', label: 'W' },
                { value: 'thursday', label: 'Th' },
                { value: 'friday', label: 'F' },
                { value: 'saturday', label: 'Sa' },
                { value: 'sunday', label: 'Su' }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.preferredRestDays?.message}
            />
            <TextareaField
              label="Any other work/life obligations that may impact your training?"
              name="otherObligations"
              register={register}
              error={errors.otherObligations?.message}
              placeholder="e.g. ski trip 4/11-4/13, primary caregiver for kids, busy work on Tuesdays"
            />
            <ToggleButtonGroup
              label="Is there anything that&apos;s made it hard to stick to a plan in the past?"
              name="pastProblems"
              options={[
                { value: 'noResults', label: "Didn't see results" },
                { value: 'noTime', label: "Didn't have time" },
                { value: 'didntUnderstand', label: "Didn't understand plan" },
                { value: 'couldntModify', label: "Couldn’t modify plan" },
                { value: 'overwhelmed', label: "Got overwhelmed" },
                { value: 'injured', label: "Got injured" },
                { value: 'notApplicable', label: "N/A" }
              ]}
              setValue={methods.setValue}
              watch={methods.watch}
              error={errors.pastProblems?.message}
            />
          </FormStep>
        )}

        {currentStep === 8 && (
          <FormStep onPrevious={previousStep} isLastStep onNext={nextStep} isLoading={isLoading}>
            <Header title="What else should I know to support you better?" subTitle="NO DETAIL IS TOO SMALL!" />
            <TextareaField
              name="moreInfo"
              register={register}
              error={errors.moreInfo?.message}
              placeholder="Share anything I may have missed. e.g. 'I had my first baby 3 months ago. I tend to injure myself from overtraining. I’m experiencing perimenopause fatigue. I take hiking trips most weekends."
              className="min-h-[150px]"
            />
          </FormStep>
        )}
      </form>
    </FormProvider>
  )
}

export default withAuth(OnboardingForm)