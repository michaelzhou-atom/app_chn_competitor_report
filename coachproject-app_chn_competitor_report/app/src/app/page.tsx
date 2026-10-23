import { AppConfigProvider } from './appcontext/appConfig';
import './components/loginForm'
import LoginForm from './components/loginForm/index';

export default function Home() {
  return (
    <>
    <AppConfigProvider>
      <div className='flex'>
        <div className="sm:w-full md:w-1/2">
          <div className="h-screen bg-cover bg-no-repeat flex flex-col justify-between" style={{ backgroundImage: `url(${'/images/loginbanner.jpg'})`}}>
            {/* <div className='p-4'>
              <img src={`/images/logo.svg`} />
            </div>
            <div className='p-4'>
              <p className='text-white md:text-[20px] font-semibold leading-tight'>Your Intelligent Document <br /> Analysis Assistant </p>
            </div> */}
          </div>
        </div>
        <div className="sm:w-full md:w-1/2">
          <div className=''>
            <LoginForm />
          </div>
        </div>
      </div>
      </AppConfigProvider>
    </>
  );
}
