export default function NotFoundContent() {
  return (
      <div className="h-screen flex flex-col items-center justify-center text-center font-sans bg-white text-black dark:bg-black dark:text-white">
          <div className="flex items-center">
              <h1 className="border-r border-black/30 dark:border-white/30 text-[24px] font-medium pr-6 mr-6 leading-[49px]">
                  404
              </h1>
              <div>
                  <h2 className="text-[14px] font-normal leading-[49px] m-0">
                  This page could not be found.
                  </h2>
              </div>
          </div>
      </div>
  )
}