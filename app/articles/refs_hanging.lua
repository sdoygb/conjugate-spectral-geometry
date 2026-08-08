-- refs_hanging.lua
-- pandoc filter: render the References block as a single paragraph with
-- hard line breaks and hanging indent (standard bibliography style).
-- Each markdown line "[n] ..." becomes one line; continuation lines are
-- indented by 2.2em; the first line is not indented.
local in_refs = false

function Header(el)
  if el.level == 2 then
    in_refs = (pandoc.utils.stringify(el.content) == "References")
  end
end

function Para(el)
  if not in_refs then return nil end
  local newc = { pandoc.RawInline('latex', '\\hangindent 2.2em\\hangafter 1 ') }
  for _, it in ipairs(el.content) do
    if it.t == "SoftBreak" then
      table.insert(newc, pandoc.LineBreak())
    else
      table.insert(newc, it)
    end
  end
  return pandoc.Para(newc)
end
