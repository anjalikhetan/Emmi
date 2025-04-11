"use client"

import withoutAuth from '@/hoc/withoutAuth';
import Image from "next/image"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form"
import { toast } from "sonner"
import { useRouter } from "next/navigation"
import { isValidPhoneNumber } from "react-phone-number-input";
import { PhoneInput } from '@/components/ui/phone-input';


// Phone number validation schema
const formSchema = z.object({
  phoneNumber: z.string().refine(isValidPhoneNumber, { message: "Invalid phone number format. Please use (XXX) XXX-XXXX" }),
})

// Header component
const Header = () => (
  <div className="relative w-full">
    <Image
      src="/landing.jpg"
      alt="Woman in white sports bra and black leggings doing yoga"
      width={1920}
      height={1080}
      className="w-full object-cover h-[40vh]" // Adjusts height dynamically
      priority
    />
    <div className="absolute inset-0 flex items-center justify-center">
      <h1 className="text-4xl md:text-5xl text-white text-center">
        <span className="font-cormorant font-semibold"><i >Hey,</i> I&rsquo;m Emmi</span>
        <span className="block text-base font-normal">YOUR PERSONAL RUNNING COACH</span>
      </h1>
    </div>
  </div>
);


// Phone Input Form component
const PhoneInputForm = () => {
  const router = useRouter()
  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      phoneNumber: "",
    },
  })

  const onSubmit = async (data) => {
    try {
      const res = await fetch(process.env.NEXT_PUBLIC_API_BASE_URL + "/api/v1/users/verification-code/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: data.phoneNumber })
      })
      const result = await res.json()
      if (res.ok) {
        // Save the phone number to use in verification page
        localStorage.setItem("phoneNumber", data.phoneNumber)
        toast("Success!", { description: "Verification code sent successfully." })
        router.push("/verification")
      } else {
        toast("Error!", { description: result.error || "Failed to send verification code." })
      }
    } catch (error) {
      toast("Error!", { description: "Unexpected error occurred." })
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="phoneNumber"
          render={({ field }) => (
            <FormItem>
              <FormControl>
                <PhoneInput
                  placeholder="Phone number"
                  defaultCountry="US"
                  countryDisabled={true}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button
          type="submit"
          className="w-full bg-[#0F213F] text-white py-3 rounded-md tracking-wider uppercase text-xs font-semibold hover:bg-[#333333] transition-all duration-300 ease-in-out transform hover:-translate-y-1"
        >
          Send
        </Button>
      </form>
    </Form>
  )
}

// Main Page component
const MainPage = () => {
  return (
    <div className="bg-white min-h-screen flex flex-col">
      <Header />
      <div className="flex-grow flex justify-center p-8">
        <div className="w-full max-w-md">
          <label className="block mt-6 text-xs tracking-wider mb-4">
            What&rsquo;s your number? I&rsquo;ll text you a training plan designed just for you.
          </label>
          <PhoneInputForm />
          <p className="text-center text-xs mt-6">
            By continuing you agree to receive messages at the phone number provided above. Message frequency will vary. Message and data rates may apply. Reply STOP to cancel.
          </p>
        </div>
      </div>
    </div>
  )
}

export default withoutAuth(MainPage);
