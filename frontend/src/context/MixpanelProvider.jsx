"use client"
import React, { createContext, useContext, useEffect } from "react"
import mixpanel from "mixpanel-browser"

const MIXPANEL_TOKEN = process.env.NEXT_PUBLIC_MIXPANEL_PROJECT_TOKEN
const MIXPANEL_ENABLED = process.env.NEXT_PUBLIC_MIXPANEL_ENABLED === "true"

const MixpanelContext = createContext(undefined)

export const MixpanelProvider = ({ children }) => {
  useEffect(() => {
    if (MIXPANEL_ENABLED && MIXPANEL_TOKEN) {
      try {
        mixpanel.init(
          MIXPANEL_TOKEN,
          {
            ignore_dnt: true 
          }
        )
      } catch (e) {
        console.error("Failed to initialize Mixpanel:", e)
      }
    }
  }, [])

  const trackEvent = (eventName, properties = {}, user = null) => {
    if (MIXPANEL_ENABLED) {
      try {
        console.log(`Tracking event: ${eventName}`)
        mixpanel.track(eventName, {
          timestamp: Date.now(),
          ...properties,
        })
        // Identify the user if provided
        if (user) {
          identify(user)
        }
      } catch (e) {
        console.error(`Error tracking event ${eventName}:`, e)
      }
    }
  }

  const identify = (user) => {
    if (MIXPANEL_ENABLED) {
      mixpanel.identify(user.id)
      mixpanel.people.set(user)
    }
  }

  const reset = () => {
    if (MIXPANEL_ENABLED) {
      mixpanel.reset()
    }
  }

  return (
    <MixpanelContext.Provider value={{ trackEvent, reset, identify }}>
      {children}
    </MixpanelContext.Provider>
  )
}

export const useMixpanel = () => {
  const context = useContext(MixpanelContext)
  if (context === undefined) {
    throw new Error("useMixpanel must be used within a MixpanelProvider")
  }
  return context
}