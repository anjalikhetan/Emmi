import { LoaderCircle } from 'lucide-react';

const LoadingScreen = () => (
    <div className="flex items-center justify-center h-screen">
        <LoaderCircle className="animate-spin" />
    </div>
)

export default LoadingScreen