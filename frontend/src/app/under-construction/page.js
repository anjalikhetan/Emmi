'use client'

const UnderConstructionPage = () => {
  return (
    <div className="flex flex-col min-h-screen bg-background border-t-8 border-[#5200FF]">
      <main className="flex flex-1 items-center justify-center px-6">
        <div className="text-center">
          <img src="/turbo-icon.svg" alt="Placeholder Logo" className="mx-auto mb-4 w-12 h-12" />
          <h1 className="text-2xl font-semibold text-foreground mb-4">
            Exciting things are on the way!
          </h1>
          <p className="text-muted-foreground text-lg">
            This section is still coming together, and we&apos;re<br /> moving fast to bring it to you
          </p>
        </div>
      </main>
    </div>
  );
}

export default UnderConstructionPage;
