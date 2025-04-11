// src/hoc/withoutAuth.js
import { useAuth } from '@/context/AuthProvider';
import { useRouter, usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { goToNextOnboardingStep } from "@/lib/utils"
import LoadingScreen from '@/components/ui/loading-screen';


const withoutAuth = (WrappedComponent) => {
  const NoAuthWrapper = (props) => {
    const { user, loadingUser } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const [isRedirecting, setIsRedirecting] = useState(true);

    useEffect(() => {
      async function redirectIfNeeded() {
        if (!loadingUser && user && user.token) {
          const redirectedToADifferentPage = await goToNextOnboardingStep(router, pathname);
          setIsRedirecting(redirectedToADifferentPage);
        }
      }
      redirectIfNeeded()
    }, [user, loadingUser, router]);

    if (loadingUser) {
      return <LoadingScreen />; // Optionally, show a loading state
    }
  
    if (user && user.token && isRedirecting) {
      // Optionally, return null if the user is authenticated,
      // this is shown temporary while the redirection is being done
      return null;
    }
  
    // Render the wrapped component with all its props
    return <WrappedComponent {...props} />;
  };

  return NoAuthWrapper;
};

export default withoutAuth;
