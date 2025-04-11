import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"
import { TOKEN_KEY } from '@/context/AuthProvider'


export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const WORKOUT_COLORS = {
  'EASY RUN': '#A3C6A8',
  'QUALITY SESSION': '#800020',
  'QUALITY RUN': '#800020',
  'LONG RUN': '#A3D4E0',
  'CROSS TRAINING': '#F2B8C4',
  'STRENGTH TRAINING': '#E1B75D',
  'STRENGTH': '#E1B75D',
  'REST AND RECOVERY': '#B497BD',
  'REST/RECOVERY': '#B497BD',
};

const DEFAULT_WORKOUT_COLOR = '#CCCCCC';

export function getWorkoutColor(type) {
  if (!type) return DEFAULT_WORKOUT_COLOR;
  return WORKOUT_COLORS[type.toUpperCase()] ?? DEFAULT_WORKOUT_COLOR;
}

export async function goToNextOnboardingStep(router, currentPath) {

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/users/me/`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Token ${localStorage.getItem(TOKEN_KEY)}`
    }
  });

  if (!response.ok) {
    console.log('Error while retrieving current user: ' + response.status);
    if (currentPath !== "/") {
      router.push("/");
      return true;
    }
    return false;
  }

  const result = await response.json();

  if (!result.is_verified) {
    console.log('User is not verified. Redirecting to phone input page...');
    if (currentPath !== "/") {
      router.push("/");
      return true;
    }
    return false;
  }

  if (!result.profile.is_onboarding_complete || !result.current_plan) {
    console.log('User has not completed onboarding. Redirecting to onboarding page...');
    if (currentPath !== "/onboarding") {
      router.push("/onboarding");
      return true;
    }
    return false;
  }

  const destination = `/plans/${result.current_plan}`;
  console.log('User is authenticated. Redirecting to dashboard of current plan...');
  if (currentPath !== destination) {
    router.push(destination);
    return true;
  }

  return false;
}
