import Image from "next/image";

export function Footer() {
  return (
    <footer className="relative mt-8 overflow-hidden rounded-[2.5rem] bg-gradient-brown px-8 py-14 text-cream">
      <Image src="/enderase-logo.png" alt="" aria-hidden width={512} height={512}
        className="pointer-events-none absolute -bottom-16 -right-10 h-72 w-72 opacity-[0.07]" />
      <div className="relative flex flex-col items-start justify-between gap-8 md:flex-row md:items-end">
        <div>
          <Image src="/enderase-logo.png" alt="Enderase Youth Association" width={48} height={48}
            className="mb-4 h-12 w-12 rounded-2xl bg-cream/95 p-1.5" />
          <h2 className="max-w-md font-display text-3xl font-extrabold leading-tight">
            Empowering Ethiopian Youth Through Data
          </h2>
          <p className="mt-2 text-cream/60">Enderase Youth Association · Registry Overview {new Date().getFullYear()}</p>
        </div>
        <div className="flex flex-wrap gap-6 text-sm text-cream/70">
          <div className="space-y-1">
            <p className="font-bold text-gold">Registry</p>
            <p>Beneficiaries</p><p>Groups</p><p>Programs</p>
          </div>
          <div className="space-y-1">
            <p className="font-bold text-gold">Insights</p>
            <p>Geography</p><p>Skills</p><p>Analytics</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
