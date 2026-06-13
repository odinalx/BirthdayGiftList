import { ref } from 'vue'

const VISITOR_NAME_KEY = 'birthday_visitor_name'
const VISITOR_ID_KEY = 'birthday_visitor_id'

function generateId(): string {
  return crypto.randomUUID()
}

function getOrCreateVisitorId(): string {
  let id = localStorage.getItem(VISITOR_ID_KEY)
  if (!id) {
    id = generateId()
    localStorage.setItem(VISITOR_ID_KEY, id)
  }
  return id
}

const visitorName = ref<string | null>(localStorage.getItem(VISITOR_NAME_KEY))
const visitorId = ref<string>(getOrCreateVisitorId())

export function useVisitor() {
  function setVisitorName(name: string) {
    visitorName.value = name
    localStorage.setItem(VISITOR_NAME_KEY, name)
  }

  function clearVisitor() {
    visitorName.value = null
    localStorage.removeItem(VISITOR_NAME_KEY)
  }

  return {
    visitorName,
    visitorId,
    setVisitorName,
    clearVisitor,
  }
}
