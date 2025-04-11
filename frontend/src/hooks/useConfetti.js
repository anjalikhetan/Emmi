import { useCallback, useEffect } from 'react'
import confetti from 'canvas-confetti'

const useConfetti = (autoStart = false) => {
    const fire = useCallback(() => {
        const count = 200
        const defaults = { origin: { y: 0.7 } }

        const trigger = (particleRatio, opts) => {
            confetti({
                ...defaults,
                ...opts,
                particleCount: Math.floor(count * particleRatio),
            })
        }

        trigger(0.25, {
            spread: 26,
            startVelocity: 55,
        })
        trigger(0.2, {
            spread: 60,
        })
        trigger(0.35, {
            spread: 100,
            decay: 0.91,
            scalar: 0.8,
        })
        trigger(0.1, {
            spread: 120,
            startVelocity: 25,
            decay: 0.92,
            scalar: 1.2,
        })
        trigger(0.1, {
            spread: 120,
            startVelocity: 45,
        })
    }, [])

    useEffect(() => {
        if (autoStart) fire()
    }, [autoStart, fire])

    return fire // you can call this manually
}

export default useConfetti
