import React, { useEffect, useRef } from 'react'
import { hydrate, render } from 'react-dom'
import { Converter, setFlavor } from 'showdown'
import xss from 'xss'
import styled from 'styled-components'
import slackifyMarkdown from 'slackify-markdown'

import { ErrorBoundary } from 'comps/error-boundary'

const converter = new Converter()
setFlavor('github')

export const MarkdownAsHtmlDisplay = ({ markdown, ...props }) => (
  <div
    dangerouslySetInnerHTML={{ __html: markdownToHtml(markdown) }}
    {...props}
  />
)

export const markdownToSlackyMarkdown = (markdownText) => {
  const slackyMarkdown = slackifyMarkdown(markdownText)
  // Sanitise HTML removing <script> tags and the like.
  // return xss(slackyMarkdown)
  return slackyMarkdown
}

export const markdownToHtml = (markdownText) => {
  const html = converter.makeHtml(markdownText)
  // Sanitise HTML removing <script> tags and the like.
  return xss(html)
}

// Skips first update
export const useEffectLazy = (func: () => void, vars: React.DependencyList) => {
  const isFirstUpdate = useRef(true)
  useEffect(() => {
    if (isFirstUpdate.current) {
      isFirstUpdate.current = false
    } else {
      func()
    }
  }, vars)
}

export const mount = (App: React.ComponentType) => {
  const root = document.getElementById('app')
  const rootComponent = (
    <ErrorBoundary>
      <FadeInOnLoad>
        <App />
      </FadeInOnLoad>
    </ErrorBoundary>
  )
  if (root.hasChildNodes()) {
    hydrate(rootComponent, root)
  } else {
    render(rootComponent, root)
  }
}

const FadeInOnLoad = styled.div`
  animation: fadein 0.3s;
  @keyframes fadein {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`

export const debounce = (delay) => {
  let timer = null
  return (func) => {
    return (...args) => {
      clearTimeout(timer)
      timer = setTimeout(() => func(...args), delay)
    }
  }
}

// Debounce user input, returns a promise
export const debouncePromise = (delay) => {
  let timer = null
  return (func) => {
    return (...args) =>
      new Promise((resolve) => {
        clearTimeout(timer)
        timer = setTimeout(() => func(...args).then(resolve), delay)
      })
  }
}

// Wait n seconds
export const waitSeconds = (delay: number) =>
  new Promise((resolve) => setTimeout(() => resolve(null), delay * 1000))

export const useOutsideClick = (ref, onClickOutside) => {
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
        onClickOutside()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [ref])
}
