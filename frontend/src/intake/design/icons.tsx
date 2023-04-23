import React from 'react'

const Error = ({ ...props }: any) => (
  <svg
    width="21"
    height="21"
    viewBox="0 0 21 21"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M17.9248 17.9248C22.0251 13.8245 22.0251 7.17546 17.9248 3.0752C13.8245 -1.02507 7.17546 -1.02507 3.0752 3.0752C-1.02507 7.17546 -1.02507 13.8245 3.0752 17.9248C7.17546 22.0251 13.8245 22.0251 17.9248 17.9248ZM9.32533 5.42454C9.59129 4.84828 10.2119 4.53799 10.8325 4.69314C11.4309 4.84828 11.8298 5.42454 11.7855 6.06728C11.7633 6.48839 11.7412 6.88733 11.719 7.30844C11.6303 8.85989 11.5417 10.4113 11.4752 11.9406C11.453 12.4504 11.0319 12.8493 10.5222 12.8493C9.99024 12.8493 9.59129 12.4504 9.56913 11.8963C9.54697 11.586 9.54697 11.2757 9.5248 10.9654C9.45831 9.96807 9.41398 8.97071 9.34749 7.95119C9.30317 7.30844 9.281 6.6657 9.23668 6.02295C9.21451 5.84565 9.23668 5.62401 9.32533 5.42454ZM10.5 13.758C11.2092 13.758 11.7855 14.3343 11.8077 15.0435C11.8077 15.7528 11.2314 16.329 10.5222 16.329C9.83509 16.329 9.23668 15.7528 9.23668 15.0657C9.21451 14.3565 9.79076 13.758 10.5 13.758Z"
      fill="#B56576"
    />
  </svg>
)

const Download = ({ ...props }: any) => (
  <svg
    width="88"
    height="68"
    viewBox="0 0 88 68"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M64 52V60H68C79.0457 60 88 51.0457 88 40C88 29.9398 80.5723 21.6145 70.9018 20.209C67.5 8.42248 56.6345 0 44 0C34.6137 0 26.0361 4.66029 20.8796 12.2011C9.06812 13.7338 0 23.8351 0 36C0 49.2548 10.7452 60 24 60V52C15.1634 52 8 44.8366 8 36C8 27.4018 14.7974 20.3486 23.3586 20.0126L25.5626 19.926L26.6657 18.0159C30.2172 11.8657 36.7696 8 44 8C53.8045 8 62.1214 15.1051 63.7238 24.6646L64.295 28.0727L67.75 28.0025C67.8122 28.0015 67.8434 28.001 67.8746 28.0006C67.9059 28.0003 67.9372 28.0002 68 28C74.6274 28 80 33.3726 80 40C80 46.6274 74.6274 52 68 52H64ZM47.9986 68V41.6569L57.1701 50.8285L62.827 45.1716L43.9986 26.3432L25.1701 45.1716L30.827 50.8285L39.9986 41.6569V68H47.9986Z"
      fill="#98D0CE"
    />
  </svg>
)

const Back = ({ ...props }: any) => (
  <svg
    width="22"
    height="39"
    viewBox="0 0 22 39"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M0.704 17.7485L17.8347 0.700599C18.832 -0.233533 20.3573 -0.233533 21.296 0.700599C22.2347 1.63473 22.2347 3.15269 21.296 4.14521L5.86667 19.5L21.296 34.8548C22.2347 35.7889 22.2347 37.3653 21.296 38.2994C20.3573 39.2335 18.832 39.2335 17.8347 38.2994L0.704 21.1931C-0.234667 20.259 -0.234667 18.741 0.704 17.7485Z"
      fill="#138799"
    />
  </svg>
)

const Close = ({ ...props }: any) => (
  <svg
    width="29"
    height="29"
    viewBox="0 0 29 29"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M17.945 14.5011L28.297 4.17875C28.7269 3.71724 28.9609 3.10684 28.9498 2.47613C28.9387 1.84542 28.6833 1.24365 28.2373 0.797605C27.7914 0.351558 27.1898 0.0960558 26.5593 0.0849277C25.9288 0.0737995 25.3185 0.307914 24.8571 0.737949L14.5052 11.0603L4.18569 0.721719C3.72739 0.261136 3.10494 0.0015286 2.45528 6.72881e-06C1.80563 -0.00151515 1.18197 0.255173 0.721517 0.713604C0.261063 1.17203 0.00152818 1.79465 6.72693e-06 2.44449C-0.00151472 3.09433 0.255102 3.71816 0.713404 4.17875L11.0654 14.5011L0.713404 24.8235C0.28349 25.285 0.0494407 25.8954 0.0605657 26.5261C0.0716907 27.1569 0.327121 27.7586 0.773044 28.2047C1.21897 28.6507 1.82057 28.9062 2.4511 28.9173C3.08163 28.9285 3.69186 28.6944 4.15324 28.2643L14.4727 17.9419L24.7922 28.2643C25.2484 28.7292 25.8705 28.9938 26.5217 28.9999C27.1728 29.006 27.7998 28.7531 28.2645 28.2968C28.7293 27.8405 28.9938 27.2182 28.9999 26.5669C29.006 25.9155 28.7531 25.2884 28.297 24.8235L17.945 14.5011Z"
      fill="#138799"
    />
  </svg>
)
const Tick = ({ color, ...props }: any) => (
  <svg
    width="18"
    height="13"
    viewBox="0 0 18 13"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M2 7L6.5 11.5L16 2"
      stroke={color || '#fff'}
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

export const Icon = {
  Download,
  Back,
  Close,
  Tick,
  Error,
}
